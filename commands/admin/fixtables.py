# ────────────────────────────────────────────────────────────────────────────────
# 📌 fixtables.py — Vérification & suggestions SQL pour Supabase (amélioré)
# Objectif : Scanner les commandes, détecter les tables/colonnes attendues par le code,
#          comparer avec la base Supabase, proposer SQL (CREATE / ALTER / ALTER TYPE)
#          et fournir une vue interactive (admin-only) pour obtenir le SQL ou tenter
#          d'exécuter les modifications (EXÉCUTION OPTIONNELLE, documentée).
# Auteur  : Généré par assistant — amélioré pour lisibilité et robustesse
# Version : 1.2 — support types, suggestions ALTER TYPE, meilleure detection
# ────────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import os
import re
import traceback
import textwrap
import discord
from discord import app_commands
from discord.ext import commands
from typing import Dict, Set, List, Tuple, Optional

from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ──────────────────────────────────────────────────────────────
# 🔧 CONFIG (modifiable)
# ──────────────────────────────────────────────────────────────
CODE_SCAN_DIR = "commands"           # dossier à scanner
WINDOW_CHARS = 2500                   # fenêtre de recherche autour de supabase.table(...)
SQL_SUGGESTION_MAX_COLS = 50          # limite pour suggestions
AUTO_EXECUTION_ALLOWED = False        # sécurité: par défaut on ne n'exécute pas le SQL
ADMIN_SQL_EXEC_RPC = "sql_exec"     # nom RPC/Postgres function optionnelle si existante

# ──────────────────────────────────────────────────────────────
# 🔎 Regex utiles pour parsing (robuste mais simple)
# ──────────────────────────────────────────────────────────────
_table_re = re.compile(r"supabase\.table\(\s*[\"']([\w\d_]+)[\"']\s*\)")
_select_re = re.compile(r"\.select\(\s*[\"']([^\"']+)[\"']\s*\)")
_eq_re = re.compile(r"\.eq\(\s*[\"']([\w\d_]+)[\"']\s*,")
_update_dict_re = re.compile(r"\.(?:update|insert)\s*\(\s*\{([^}]+)\}", re.S)
_insert_dict_re = re.compile(r"\.insert\s*\(\s*\{([^}]+)\}", re.S)
_key_in_dict_re = re.compile(r"[\"']([\w\d_]+)[\"']\s*:")

# ──────────────────────────────────────────────────────────────
# 🧠 Heuristiques de type SQL (proposition)
# ──────────────────────────────────────────────────────────────
def _infer_sql_type(column_name: str) -> str:
    cn = column_name.lower()
    # Identifiants/textes
    if cn.endswith("_id") or cn in {"user_id", "guild_id", "channel_id", "message_id", "id_faux_reiatsu"}:
        return "text"
    # Entiers
    if cn in {"points", "spawn_delay", "delay_minutes", "skill_cd", "bonus5", "skill_cd", "spawn_message_id"}:
        return "integer"
    # Timestamps
    if cn.endswith("_at") or cn.startswith("last_") or cn in {"created_at", "last_spawn_at", "last_skill"}:
        return "timestamp with time zone"
    # Booléens
    if cn in {"en_attente", "has_skill", "active"} or cn.startswith("is_") or cn.startswith("has_"):
        return "boolean"
    # JSON
    if "json" in cn or "data" in cn or cn in {"active_skill"}:
        return "jsonb"
    # Text par défaut
    return "text"

# ──────────────────────────────────────────────────────────────
# 📦 Helpers supabase — parsing des retours
# ──────────────────────────────────────────────────────────────
def _parse_result(res) -> Tuple[Optional[list], Optional[object]]:
    try:
        if res is None:
            return None, None
        if hasattr(res, "data") or hasattr(res, "error"):
            data = getattr(res, "data", None)
            err = getattr(res, "error", None)
            return data, err
        if isinstance(res, dict):
            return res.get("data"), res.get("error")
        return None, None
    except Exception:
        return None, None

# ──────────────────────────────────────────────────────────────
# 🔍 Découverte des tables/colonnes via scanning du code
# ──────────────────────────────────────────────────────────────
def discover_expected_tables(commands_dir: str = CODE_SCAN_DIR) -> Dict[str, Dict]:
    results: Dict[str, Dict] = {}
    for root, _, files in os.walk(commands_dir):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    code = fh.read()
            except Exception:
                continue

            for match in _table_re.finditer(code):
                table = match.group(1)
                start_pos = match.end()
                line_no = code[:match.start()].count("\n") + 1
                tbl_info = results.setdefault(table, {"columns": {}, "locations": []})
                tbl_info["locations"].append((path, line_no))

                window = code[start_pos:start_pos + WINDOW_CHARS]

                # .select('a,b,c')
                for s in _select_re.finditer(window):
                    cols_raw = s.group(1)
                    if cols_raw.strip() == "*":
                        continue
                    for col in cols_raw.split(","):
                        c = col.strip().strip("`\"'")
                        if c:
                            tbl_info["columns"].setdefault(c, []).append((path, line_no))

                # .eq('col', ...)
                for e in _eq_re.finditer(window):
                    c = e.group(1)
                    tbl_info["columns"].setdefault(c, []).append((path, line_no))

                # update/insert dict keys
                for block in _update_dict_re.finditer(window):
                    block_text = block.group(1)
                    for k in _key_in_dict_re.findall(block_text):
                        tbl_info["columns"].setdefault(k, []).append((path, line_no))
                for block in _insert_dict_re.finditer(window):
                    block_text = block.group(1)
                    for k in _key_in_dict_re.findall(block_text):
                        tbl_info["columns"].setdefault(k, []).append((path, line_no))
    return results

# ──────────────────────────────────────────────────────────────
# 🗄️ Lecture structurelle depuis Supabase
# ──────────────────────────────────────────────────────────────
def fetch_actual_columns(table_name: str) -> Tuple[Optional[Set[str]], Optional[Dict[str,str]], Optional[str]]:
    """
    Retourne (set(columns), dict(column->type) or None, error_message)
    - Si table inexistante -> (None, None, error)
    - Si table existe mais vide -> (set(), None, None) ou (set(cols), types, None)
    """
    try:
        # 1) Essayer d'obtenir un échantillon de ligne pour déduire les colonnes
        res = supabase.table(table_name).select("*").limit(1).execute()
        data, err = _parse_result(res)
        if err:
            return None, None, str(err)
        if data is None:
            # fallback : table vide ou pas accessible -> essayer info schema via postgrest
            pass
        else:
            if isinstance(data, list) and len(data) > 0:
                row = data[0]
                if isinstance(row, dict):
                    # colonnes + pas de types fiables à partir de l'API -> types None
                    return set(row.keys()), None, None
            # table vide -> tenter info_schema

        # 2) Tenter de récupérer les colonnes via information_schema (si PostgREST l'expose)
        try:
            isc = supabase.postgrest.from_("information_schema.columns").select("column_name,data_type,udt_name").eq("table_name", table_name).execute()
            isc_data, isc_err = _parse_result(isc)
            if isc_err:
                # pas exposé - on retourne table vide
                return set(), None, None
            if isc_data and isinstance(isc_data, list):
                cols = set()
                types = {}
                for r in isc_data:
                    cname = r.get("column_name")
                    dtype = r.get("data_type") or r.get("udt_name")
                    if cname:
                        cols.add(cname)
                        types[cname] = dtype
                return cols, types, None
        except Exception:
            # information_schema peut ne pas être accessible via PostgREST
            pass

        # 3) Si tout échoue on retourne table vide (existence incertaine)
        # mais on a déjà essayé de select -> si aucune erreur et pas de données -> table existe mais vide
        return set(), None, None
    except Exception as e:
        return None, None, str(e)

# ──────────────────────────────────────────────────────────────
# 🧾 Génération SQL (suggestions)
# ──────────────────────────────────────────────────────────────
def suggest_create_table_sql(table: str, columns: Set[str]) -> str:
    if not columns:
        return f"-- Suggestion: CREATE TABLE {table} ( /* définir colonnes */ );"

    cols_lines = []
    for c in list(columns)[:SQL_SUGGESTION_MAX_COLS]:
        t = _infer_sql_type(c)
        default = ""
        if t.startswith("timestamp"):
            default = " DEFAULT now()"
        cols_lines.append(f"  {c} {t}{default}")
    pk = next(iter(columns))
    body = ",\n".join(cols_lines)
    sql = f"CREATE TABLE IF NOT EXISTS {table} (\n{body},\n  CONSTRAINT {table}_pkey PRIMARY KEY ({pk})\n);"
    return sql


def suggest_alter_table_add_columns_sql(table: str, missing: Set[str]) -> str:
    if not missing:
        return "-- Aucune colonne manquante."
    stmts = []
    for c in missing:
        t = _infer_sql_type(c)
        stmts.append(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {c} {t};")
    return "\n".join(stmts)


def suggest_alter_column_type_sql(table: str, col: str, to_type: str) -> str:
    # Note: ALTER TYPE peut nécessiter USING clause selon conversions — simple suggestion
    return f"ALTER TABLE {table} ALTER COLUMN {col} TYPE {to_type} USING {col}::{to_type};"

# ──────────────────────────────────────────────────────────────
# 🎛️ Vue interactive — boutons pour afficher / appliquer les corrections
# ──────────────────────────────────────────────────────────────
class FixTablesView(discord.ui.View):
    def __init__(self, missing_tables: List[str], corrections: List[Tuple[str, Set[str]]], type_mismatches: List[Tuple[str,str,str]]):
        super().__init__(timeout=180)
        self.missing_tables = missing_tables
        self.corrections = corrections
        self.type_mismatches = type_mismatches

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator

    @discord.ui.button(label="Afficher SQL (CREATE)", style=discord.ButtonStyle.success, custom_id="ft_create_sql")
    async def _create_sql(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        blocks = []
        for t in self.missing_tables:
            cols = set()
            for (tbl, missing) in self.corrections:
                if tbl == t:
                    cols = missing
                    break
            blocks.append(f"-- CREATE TABLE suggestion pour `{t}`\n{suggest_create_table_sql(t, cols)}")
        content = "\n\n".join(blocks) or "Aucune table manquante."
        await interaction.followup.send(f"```sql\n{content}\n```", ephemeral=True)

    @discord.ui.button(label="Afficher SQL (ALTER ADD)", style=discord.ButtonStyle.primary, custom_id="ft_alter_sql")
    async def _alter_sql(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        parts = []
        for table, missing in self.corrections:
            if not missing:
                continue
            parts.append(f"-- ALTER TABLE pour `{table}`\n{suggest_alter_table_add_columns_sql(table, missing)}")
        if not parts:
            await interaction.followup.send("Aucune colonne manquante détectée.", ephemeral=True)
            return
        await interaction.followup.send(f"```sql\n{'\n\n'.join(parts)}\n```", ephemeral=True)

    @discord.ui.button(label="Afficher SQL (ALTER TYPE)", style=discord.ButtonStyle.secondary, custom_id="ft_alter_type")
    async def _alter_type(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        parts = []
        for table, col, suggested in self.type_mismatches:
            parts.append(f"-- ALTER TYPE pour `{table}`.{col}\n{suggest_alter_column_type_sql(table, col, suggested)}")
        if not parts:
            await interaction.followup.send("Aucune incompatibilité de type détectée.", ephemeral=True)
            return
        await interaction.followup.send(f"```sql\n{'\n\n'.join(parts)}\n```", ephemeral=True)

    @discord.ui.button(label="(OPTION) Appliquer ALTER ADD", style=discord.ButtonStyle.danger, custom_id="ft_apply_alter", row=3)
    async def _apply_alter(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Sécurité : n'exécute que si AUTO_EXECUTION_ALLOWED True ou si RPC administratif existe
        await interaction.response.defer(ephemeral=True, thinking=True)
        if not AUTO_EXECUTION_ALLOWED:
            await interaction.followup.send("⚠️ Exécution automatique désactivée sur cette instance. Active AUTO_EXECUTION_ALLOWED si tu veux autoriser.", ephemeral=True)
            return
        # Construire et appliquer
        all_stmts = []
        for table, missing in self.corrections:
            if missing:
                all_stmts.append(suggest_alter_table_add_columns_sql(table, missing))
        sql = "\n".join(all_stmts)
        if not sql:
            await interaction.followup.send("Rien à appliquer.", ephemeral=True)
            return
        try:
            # Tentative d'exécution via RPC POSTGRES (nécessite création d'une fn sql_exec côté DB)
            res = supabase.rpc(ADMIN_SQL_EXEC_RPC, {"p_sql": sql}).execute()
            data, err = _parse_result(res)
            if err:
                await interaction.followup.send(f"❌ Erreur lors de l'exécution : {err}", ephemeral=True)
            else:
                await interaction.followup.send("✅ SQL appliqué (voir résultat du RPC).", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Impossible d'exécuter le SQL automatiquement : {e}\n\nTu peux utiliser les SQL fournis manuellement dans ton client Supabase.", ephemeral=True)

# ──────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ──────────────────────────────────────────────────────────────
class FixTables(commands.Cog):
    """
    /fixtables & !fixtables — Analyse et suggestions SQL non destructives pour Supabase

    - Scanne le dossier `commands/` pour trouver les appels `supabase.table(...)`.
    - Détermine les colonnes attendues (select, eq, insert/update dict keys, ...).
    - Interroge Supabase pour récupérer colonnes & types (si possible).
    - Produit un rapport lisible et des suggestions SQL.
    - Option (ADMIN) : tenter d'exécuter SQL via un RPC nommé (sécurisé & optionnel).
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _scan_and_report(self, channel: discord.abc.Messageable, verbose: bool = False):
        try:
            expected = discover_expected_tables(CODE_SCAN_DIR)
            if not expected:
                await safe_send(channel, "❌ Aucune utilisation de `supabase.table(...)` détectée dans le dossier `commands/`.")
                return

            embed = discord.Embed(
                title="🔎 Rapport fixtables",
                description="Comparaison code ←→ Supabase. (Suggestions non-destructives affichées)",
                color=discord.Color.blurple()
            )

            missing_tables = []
            corrections: List[Tuple[str, Set[str]]] = []
            type_mismatches: List[Tuple[str,str,str]] = []

            for table, info in expected.items():
                expected_cols = set(info.get("columns", {}).keys())
                actual_cols, actual_types, error = fetch_actual_columns(table)

                # Table absente ou erreur
                if actual_cols is None:
                    missing_tables.append(table)
                    location_lines = "\n".join([f"- `{p}`:{ln}" for p, ln in info.get("locations", [])[:6]])
                    embed.add_field(
                        name=f"❌ `{table}` — absente / erreur",
                        value=(
                            f"• Colonnes attendues ({len(expected_cols)}): `{', '.join(sorted(expected_cols)) or 'Aucune détectée'}`\n"
                            f"• Emplacements (quelques uns) :\n{location_lines}\n"
                            f"• Note Supabase : `{error}`\n\n"
                            f"→ Suggestion CREATE TABLE : (voir bouton 'Afficher SQL (CREATE)')"
                        ),
                        inline=False
                    )
                    continue

                # Table existante
                actual_cols = actual_cols or set()
                missing = expected_cols - actual_cols
                extra = actual_cols - expected_cols

                # vérification de type (si actual_types fourni)
                mismatch_lines = []
                if actual_types:
                    # actual_types: dict col->type
                    for col in expected_cols & actual_cols:
                        expected_type = _infer_sql_type(col)
                        actual_type = actual_types.get(col)
                        if actual_type and expected_type and expected_type.split()[0] not in actual_type:
                            # heuristique : si mot clé du type attendu n'est pas dans actual_type
                            mismatch_lines.append((col, actual_type, expected_type))
                            type_mismatches.append((table, col, expected_type))

                if not missing and not extra and not mismatch_lines:
                    embed.add_field(name=f"✅ `{table}`", value="Structure conforme ✅", inline=False)
                else:
                    parts = []
                    if missing:
                        corrections.append((table, missing))
                        parts.append(f"⚠️ Colonnes manquantes ({len(missing)}): `{', '.join(sorted(missing))}`")
                        parts.append("```sql\n" + suggest_alter_table_add_columns_sql(table, missing) + "\n```")
                    if extra:
                        parts.append(f"ℹ️ Colonnes supplémentaires ({len(extra)}): `{', '.join(sorted(extra))}`")
                    if mismatch_lines:
                        mtxt = []
                        for c, at, et in mismatch_lines:
                            mtxt.append(f"• `{c}` attendu `{et}` mais trouvé `{at}`")
                        parts.append("⚠️ Incompatibilités de type:\n" + "\n".join(mtxt))
                        # ajouter suggestions ALTER TYPE
                        parts.append("```sql\n" + "\n\n".join([suggest_alter_column_type_sql(table, c, et) for c, at, et in mismatch_lines]) + "\n```")

                    embed.add_field(name=f"⚠️ `{table}`", value="\n".join(parts), inline=False)

            view = FixTablesView(missing_tables, corrections, type_mismatches) if (missing_tables or corrections or type_mismatches) else None
            await safe_send(channel, embed=embed, view=view)

            if verbose:
                # Détails mapping colonne -> occurrences
                detail_msg = []
                for table, info in expected.items():
                    lines = []
                    for col, occs in info.get("columns", {}).items():
                        refs = ", ".join([f"{os.path.relpath(p)}:{ln}" for p, ln in occs[:3]])
                        lines.append(f"- {col} (ex: {refs})")
                    if lines:
                        detail_msg.append(f"**{table}**\n" + "\n".join(lines))
                if detail_msg:
                    chunk = "\n\n".join(detail_msg)
                    await safe_send(channel, f"**Détails (verbose)**\n{chunk}")

        except Exception as e:
            tb = traceback.format_exc()
            print("[fixtables] ERREUR:", tb)
            await safe_send(channel, f"❌ Une erreur est survenue pendant l'analyse.\n```py\n{tb[:1900]}\n```")

    # ──────────────────────────────────────────────────────────
    # Slash
    # ──────────────────────────────────────────────────────────
    @app_commands.command(name="fixtables", description="🔧 Analyse & suggestions SQL pour les tables Supabase")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: (i.guild_id or i.user.id))
    async def slash_fixtables(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            await self._scan_and_report(interaction.channel, verbose=False)
            await interaction.followup.send("✅ Rapport généré (épinglé dans le canal).", ephemeral=True)
        except Exception:
            tb = traceback.format_exc()
            print("[fixtables] ERREUR (slash):", tb)
            await safe_respond(interaction, f"❌ Une erreur est survenue :\n```py\n{tb[:1500]}\n```", ephemeral=True)

    # ──────────────────────────────────────────────────────────
    # Prefix
    # ──────────────────────────────────────────────────────────
    @commands.command(name="fixtables")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 30.0, commands.BucketType.guild)
    async def prefix_fixtables(self, ctx: commands.Context):
        await self._scan_and_report(ctx.channel, verbose=False)

# ──────────────────────────────────────────────────────────────
# 🔌 Setup
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = FixTables(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
