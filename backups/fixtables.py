# ────────────────────────────────────────────────────────────────────────────────
# 📌 fixtables.py — Vérification & suggestions SQL pour Supabase
# ────────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 Imports
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
# 🔧 Config
# ──────────────────────────────────────────────────────────────
CODE_SCAN_DIR = "commands"   # dossier à scanner
WINDOW_CHARS = 2500         # recherche locale autour du supabase.table(...) call
SQL_SUGGESTION_MAX_COLS = 30

# ──────────────────────────────────────────────────────────────
# 🔎 Helpers — parsing robust
# ──────────────────────────────────────────────────────────────
_table_re = re.compile(r'supabase\.table\(\s*["\']([\w\d_]+)["\']\s*\)')
_select_re = re.compile(r'\.select\(\s*["\']([^"\']+)["\']\s*\)')
_eq_re = re.compile(r'\.eq\(\s*["\']([\w\d_]+)["\']\s*,')
_update_dict_re = re.compile(r'\.(?:update|insert)\s*\(\s*\{([^}]+)\}', re.S)
_insert_dict_re = re.compile(r'\.insert\s*\(\s*\{([^}]+)\}', re.S)
_key_in_dict_re = re.compile(r'["\']([\w\d_]+)["\']\s*:')

def _infer_sql_type(column_name: str) -> str:
    """
    Heuristique simple pour proposer un type SQL quand la table est manquante.
    C'est une suggestion — à vérifier avant exécution.
    """
    cn = column_name.lower()
    if cn.endswith("_id") or cn in {"user_id", "guild_id", "channel_id", "message_id", "id_faux_reiatsu"}:
        # IDs en texte pour éviter overflow interop — admin peut convertir en bigint si besoin
        return "text"
    if cn in {"points", "spawn_delay", "delay_minutes", "skill_cd", "spawn_message_id", "id_faux_reiatsu"}:
        return "integer"
    if cn.endswith("_at") or cn.startswith("last_") or cn in {"created_at", "last_spawn_at", "last_skill"}:
        return "timestamp with time zone"
    if cn in {"en_attente", "has_skill", "active"} or cn.startswith("is_") or cn.startswith("has_"):
        return "boolean"
    if "json" in cn or "data" in cn or cn in {"active_skill"}:
        return "jsonb"
    if cn in {"username", "pouvoir", "classe", "spawn_speed"}:
        return "text"
    # fallback
    return "text"

def _parse_result(res) -> Tuple[Optional[list], Optional[object]]:
    """
    Récupère data, error de façon robuste depuis le client supabase (objet/dict).
    """
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
# 🔍 Découverte des tables attendues (plus fiable)
# ──────────────────────────────────────────────────────────────
def discover_expected_tables(commands_dir: str = CODE_SCAN_DIR) -> Dict[str, Dict]:
    """
    Parcourt les fichiers .py et identifie les appels supabase.table("name").
    Pour chaque occurrence on cherche, dans une fenêtre après l'appel, les .select/.eq/.update/.insert
    et on collecte les colonnes attendues + fichier/ligne d'apparition.
    Retour :
        {
            "table_name": {
                "columns": {
                    "col_name": [("path/file.py", line_no), ...],
                    ...
                },
                "locations": [("path/file.py", line_no), ...]  # où la table est référencée
            }, ...
        }
    """
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
                # ligne approximative
                line_no = code[:match.start()].count("\n") + 1
                tbl_info = results.setdefault(table, {"columns": {}, "locations": []})
                tbl_info["locations"].append((path, line_no))

                window = code[start_pos:start_pos + WINDOW_CHARS]

                # select(...) -> list of columns (comma separated)
                for s in _select_re.finditer(window):
                    cols_raw = s.group(1)
                    if cols_raw.strip() == "*":
                        continue
                    for col in cols_raw.split(","):
                        c = col.strip().strip("`\"'")
                        if c:
                            tbl_info["columns"].setdefault(c, []).append((path, line_no))

                # .eq("col", ...)
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
# 🗄️ Lecture de la structure réelle depuis Supabase
# ──────────────────────────────────────────────────────────────
def fetch_actual_columns(table_name: str) -> Tuple[Optional[Set[str]], Optional[str]]:
    """
    Retourne (set(columns), None) si la table existe (même vide),
    (None, error_message) si erreur / table inexistante.
    """
    try:
        res = supabase.table(table_name).select("*").limit(1).execute()
        data, err = _parse_result(res)
        if err:
            # si erreur SQL : prob table inexistante ou autre
            return None, str(err)
        # si data None mais pas d'erreur : table peut exister mais vide => tenter schéma via information_schema ?
        if data is None:
            # on essaie néanmoins de retourner un set vide (table existante mais vide)
            return set(), None
        if isinstance(data, list) and len(data) == 0:
            # table existe mais vide -> on récupère colonnes via supabase RPC? -> fallback : empty set
            return set(), None
        # sinon on a un dict / row
        row = data[0] if isinstance(data, list) else data
        if isinstance(row, dict):
            return set(row.keys()), None
        return set(), None
    except Exception as e:
        # erreur réseau / client / SQL -> on renvoie l'erreur pour debug
        return None, str(e)

# ──────────────────────────────────────────────────────────────
# 🧾 Génération SQL de suggestion (non exécuté)
# ──────────────────────────────────────────────────────────────
def suggest_create_table_sql(table: str, columns: Set[str]) -> str:
    """
    Propose un CREATE TABLE basé sur heuristique. C'est une suggestion — à personnaliser.
    """
    if not columns:
        return f"-- Suggestion: CREATE TABLE {table} ( /* définir colonnes */ );"

    cols_lines = []
    for c in list(columns)[:SQL_SUGGESTION_MAX_COLS]:
        t = _infer_sql_type(c)
        default = ""
        if t.startswith("timestamp"):
            default = " DEFAULT now()"
        cols_lines.append(f"  {c} {t}{default}")
    body = ",\n".join(cols_lines)
    sql = f"CREATE TABLE IF NOT EXISTS {table} (\n{body},\n  CONSTRAINT {table}_pkey PRIMARY KEY ({next(iter(columns))})\n);"
    return sql

def suggest_alter_table_add_columns_sql(table: str, missing: Set[str]) -> str:
    if not missing:
        return "-- Aucune colonne manquante."
    stmts = []
    for c in missing:
        t = _infer_sql_type(c)
        stmts.append(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {c} {t};")
    return "\n".join(stmts)

# ──────────────────────────────────────────────────────────────
# 🎛️ Vue interactive (boutons simulés) — sécurité admin
# ──────────────────────────────────────────────────────────────
class FixTablesView(discord.ui.View):
    def __init__(self, missing_tables: List[str], corrections: List[Tuple[str, Set[str]]]):
        super().__init__(timeout=120)
        self.missing_tables = missing_tables
        self.corrections = corrections

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator

    @discord.ui.button(label="Générer SQL (création)", style=discord.ButtonStyle.success, custom_id="ft_create_sql")
    async def _create_sql(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Envoi des CREATE TABLE suggérés (simulation) — éphémère.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)
        blocks = []
        for t in self.missing_tables:
            # on doit redemander les colonnes attendues — pour simplicité on dit "voir le rapport principal"
            blocks.append(f"-- CREATE TABLE suggestion pour `{t}` (colonnes détectées dans le code)\n-- Voir rapport principal pour colonnes détaillées.")
        content = "\n\n".join(blocks) or "Aucune table manquante."
        await interaction.followup.send(f"```sql\n{content}\n```", ephemeral=True)

    @discord.ui.button(label="Générer SQL (ALTER ADD)", style=discord.ButtonStyle.primary, custom_id="ft_alter_sql")
    async def _alter_sql(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Envoi des ALTER TABLE ... ADD COLUMN pour les colonnes manquantes (simulation)
        """
        await interaction.response.defer(ephemeral=True, thinking=True)
        parts = []
        for table, missing in self.corrections:
            if not missing:
                continue
            parts.append(f"-- ALTER TABLE pour `{table}`\n{suggest_alter_table_add_columns_sql(table, missing)}")
        if not parts:
            await interaction.followup.send("Aucune colonne manquante détectée.", ephemeral=True)
            return
        await interaction.followup.send(f"```sql\n{'\n\n'.join(parts)}\n```", ephemeral=True)

# ──────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ──────────────────────────────────────────────────────────────
class FixTables(commands.Cog):
    """
    /fixtables & !fixtables — Analyse et suggestions SQL non destructives pour Supabase
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
            corrections = []  # list of (table, set(missing_cols))

            for table, info in expected.items():
                expected_cols = set(info.get("columns", {}).keys())
                actual_cols, error = fetch_actual_columns(table)

                # Si error not None => table probablement inexistante ou accès refusé
                if actual_cols is None:
                    missing_tables.append(table)
                    location_lines = "\n".join([f"- `{p}`:{ln}" for p, ln in info.get("locations", [])[:6]])
                    embed.add_field(
                        name=f"❌ `{table}` — absente / erreur",
                        value=(
                            f"• Colonnes attendues ({len(expected_cols)}): `{', '.join(sorted(expected_cols)) or 'Aucune détectée'}`\n"
                            f"• Emplacements (quelques uns) :\n{location_lines}\n"
                            f"• Erreur / note Supabase : `{error}`\n\n"
                            f"→ Suggestion CREATE TABLE : (voir le bouton « Générer SQL (création) »)"
                        ),
                        inline=False
                    )
                    continue

                # existing table
                missing = expected_cols - actual_cols
                extra = actual_cols - expected_cols
                if not missing and not extra:
                    embed.add_field(name=f"✅ `{table}`", value="Structure conforme ✅", inline=False)
                else:
                    val_lines = []
                    if missing:
                        corrections.append((table, missing))
                        val_lines.append(f"⚠️ Colonnes manquantes ({len(missing)}): `{', '.join(sorted(missing))}`")
                        # ajouter SQL suggestion
                        val_lines.append("```sql\n" + suggest_alter_table_add_columns_sql(table, missing) + "\n```")
                    if extra:
                        val_lines.append(f"ℹ️ Colonnes supplémentaires ({len(extra)}): `{', '.join(sorted(extra))}`")
                    embed.add_field(name=f"⚠️ `{table}`", value="\n".join(val_lines), inline=False)

            view = FixTablesView(missing_tables, corrections) if (missing_tables or corrections) else None
            await safe_send(channel, embed=embed, view=view)

            # mode verbose: envoyer aussi le mapping fichier:ligne -> colonnes détectées
            if verbose:
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
                    # si long, on envoie en message séparé
                    await safe_send(channel, f"**Détails (verbose)**\n{chunk}")

        except Exception as e:
            tb = traceback.format_exc()
            print("[fixtables] ERREUR:", tb)
            # envoyer le traceback à l'admin de façon éphémère pour debug
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
            # si admin veux verbose: /fixtables verbose:True (non implémenté en app_command ci-dessous)
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
