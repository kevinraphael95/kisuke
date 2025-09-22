# ────────────────────────────────────────────────────────────────────────────────
# 📌 fixtables.py — Vérification & modifications SQL pour Supabase (admin)
# Objectif : Scanner les commandes, détecter tables/colonnes attendues, comparer
#           avec Supabase, proposer SQL CREATE / ALTER / ALTER TYPE et exécution.
# Auteur  : Assistant amélioré
# Version : 1.2
# ────────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import os
import re
import traceback
import discord
from discord import app_commands
from discord.ext import commands
from typing import Dict, Set, List, Tuple, Optional
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ──────────────────────────────────────────────────────────────
# 🔧 CONFIG
# ──────────────────────────────────────────────────────────────
CODE_SCAN_DIR = "commands"
WINDOW_CHARS = 2500
SQL_SUGGESTION_MAX_COLS = 50
AUTO_EXECUTION_ALLOWED = False  # ⚠️ Ne pas exécuter automatiquement si False
ADMIN_SQL_EXEC_RPC = "sql_exec"  # RPC pour exécuter SQL côté Supabase si existant

# ──────────────────────────────────────────────────────────────
# 🔎 REGEX PARSING
# ──────────────────────────────────────────────────────────────
_table_re = re.compile(r"supabase\.table\(\s*[\"']([\w\d_]+)[\"']\s*\)")
_select_re = re.compile(r"\.select\(\s*[\"']([^\"']+)[\"']\s*\)")
_eq_re = re.compile(r"\.eq\(\s*[\"']([\w\d_]+)[\"']\s*,")
_update_dict_re = re.compile(r"\.(?:update|insert)\s*\(\s*\{([^}]+)\}", re.S)
_insert_dict_re = re.compile(r"\.insert\s*\(\s*\{([^}]+)\}", re.S)
_key_in_dict_re = re.compile(r"[\"']([\w\d_]+)[\"']\s*:")

# ──────────────────────────────────────────────────────────────
# 🧠 HEURISTIQUES TYPE SQL
# ──────────────────────────────────────────────────────────────
def _infer_sql_type(column_name: str) -> str:
    cn = column_name.lower()
    if cn.endswith("_id") or cn in {"user_id", "guild_id", "channel_id", "message_id"}:
        return "text"
    if cn in {"points", "spawn_delay", "delay_minutes", "skill_cd", "spawn_message_id"}:
        return "integer"
    if cn.endswith("_at") or cn.startswith("last_") or cn in {"created_at", "last_spawn_at"}:
        return "timestamp with time zone"
    if cn in {"active", "has_skill"} or cn.startswith("is_") or cn.startswith("has_"):
        return "boolean"
    if "json" in cn or "data" in cn:
        return "jsonb"
    return "text"

# ──────────────────────────────────────────────────────────────
# 📦 HELPER SUPABASE
# ──────────────────────────────────────────────────────────────
def _parse_result(res) -> Tuple[Optional[list], Optional[object]]:
    try:
        if res is None:
            return None, None
        if hasattr(res, "data") or hasattr(res, "error"):
            return getattr(res, "data", None), getattr(res, "error", None)
        if isinstance(res, dict):
            return res.get("data"), res.get("error")
        return None, None
    except Exception:
        return None, None

# ──────────────────────────────────────────────────────────────
# 🔍 DISCOVER TABLES
# ──────────────────────────────────────────────────────────────
def discover_expected_tables(commands_dir: str = CODE_SCAN_DIR) -> Dict[str, Dict]:
    results: Dict[str, Dict] = {}
    for root, _, files in os.walk(commands_dir):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            try:
                code = open(path, "r", encoding="utf-8").read()
            except Exception:
                continue

            for match in _table_re.finditer(code):
                table = match.group(1)
                start_pos = match.end()
                line_no = code[:match.start()].count("\n") + 1
                tbl_info = results.setdefault(table, {"columns": {}, "locations": []})
                tbl_info["locations"].append((path, line_no))
                window = code[start_pos:start_pos + WINDOW_CHARS]

                for s in _select_re.finditer(window):
                    cols_raw = s.group(1)
                    if cols_raw.strip() == "*":
                        continue
                    for col in cols_raw.split(","):
                        c = col.strip().strip("`\"'")
                        if c:
                            tbl_info["columns"].setdefault(c, []).append((path, line_no))
                for e in _eq_re.finditer(window):
                    c = e.group(1)
                    tbl_info["columns"].setdefault(c, []).append((path, line_no))
                for block in _update_dict_re.finditer(window):
                    for k in _key_in_dict_re.findall(block.group(1)):
                        tbl_info["columns"].setdefault(k, []).append((path, line_no))
                for block in _insert_dict_re.finditer(window):
                    for k in _key_in_dict_re.findall(block.group(1)):
                        tbl_info["columns"].setdefault(k, []).append((path, line_no))
    return results

# ──────────────────────────────────────────────────────────────
# 🗄️ FETCH ACTUAL COLUMNS
# ──────────────────────────────────────────────────────────────
def fetch_actual_columns(table_name: str) -> Tuple[Optional[Set[str]], Optional[Dict[str,str]], Optional[str]]:
    try:
        res = supabase.table(table_name).select("*").limit(1).execute()
        data, err = _parse_result(res)
        if err:
            return None, None, str(err)
        cols = set()
        types = {}
        if data and isinstance(data, list) and len(data) > 0:
            row = data[0]
            if isinstance(row, dict):
                cols = set(row.keys())
        # fallback info_schema
        try:
            isc = supabase.postgrest.from_("information_schema.columns").select("column_name,data_type").eq("table_name", table_name).execute()
            isc_data, isc_err = _parse_result(isc)
            if isc_err is None and isc_data:
                for r in isc_data:
                    cname = r.get("column_name")
                    dtype = r.get("data_type")
                    if cname:
                        cols.add(cname)
                        types[cname] = dtype
        except Exception:
            pass
        return cols, types or None, None
    except Exception as e:
        return None, None, str(e)

# ──────────────────────────────────────────────────────────────
# 🧾 GENERATION SQL
# ──────────────────────────────────────────────────────────────
def suggest_create_table_sql(table: str, columns: Set[str]) -> str:
    if not columns:
        return f"-- CREATE TABLE {table} (/* colonnes à définir */);"
    lines = []
    for c in list(columns)[:SQL_SUGGESTION_MAX_COLS]:
        t = _infer_sql_type(c)
        default = " DEFAULT now()" if t.startswith("timestamp") else ""
        lines.append(f"  {c} {t}{default}")
    pk = next(iter(columns))
    return f"CREATE TABLE IF NOT EXISTS {table} (\n{',\n'.join(lines)},\n  CONSTRAINT {table}_pkey PRIMARY KEY ({pk})\n);"

def suggest_alter_table_add_columns_sql(table: str, missing: Set[str]) -> str:
    return "\n".join([f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {c} {_infer_sql_type(c)};" for c in missing])

def suggest_alter_column_type_sql(table: str, col: str, to_type: str) -> str:
    return f"ALTER TABLE {table} ALTER COLUMN {col} TYPE {to_type} USING {col}::{to_type};"

# ──────────────────────────────────────────────────────────────
# 🎛️ VIEW INTERACTIVE
# ──────────────────────────────────────────────────────────────
class FixTablesView(discord.ui.View):
    def __init__(self, missing_tables: List[str], corrections: List[Tuple[str, Set[str]]], type_mismatches: List[Tuple[str,str,str]]):
        super().__init__(timeout=180)
        self.missing_tables = missing_tables
        self.corrections = corrections
        self.type_mismatches = type_mismatches

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator

    @discord.ui.button(label="Afficher SQL (CREATE)", style=discord.ButtonStyle.success)
    async def create_sql(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        blocks = [f"-- CREATE TABLE {t}\n{suggest_create_table_sql(t, set())}" for t in self.missing_tables]
        await interaction.followup.send(f"```sql\n{'\n\n'.join(blocks)}\n```", ephemeral=True)

    @discord.ui.button(label="Afficher SQL (ALTER ADD)", style=discord.ButtonStyle.primary)
    async def alter_sql(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        parts = [f"-- ALTER TABLE {table}\n{suggest_alter_table_add_columns_sql(table, missing)}" for table, missing in self.corrections if missing]
        await interaction.followup.send(f"```sql\n{'\n\n'.join(parts)}\n```", ephemeral=True)

    @discord.ui.button(label="Afficher SQL (ALTER TYPE)", style=discord.ButtonStyle.secondary)
    async def alter_type(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        parts = [f"-- ALTER TYPE {table}.{col}\n{suggest_alter_column_type_sql(table,col,to_type)}" for table,col,to_type in self.type_mismatches]
        await interaction.followup.send(f"```sql\n{'\n\n'.join(parts)}\n```", ephemeral=True)

    @discord.ui.button(label="Appliquer ALTER ADD (optionnel)", style=discord.ButtonStyle.danger)
    async def apply_alter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True, thinking=True)
        if not AUTO_EXECUTION_ALLOWED:
            await interaction.followup.send("⚠️ Exécution automatique désactivée.", ephemeral=True)
            return
        sql = "\n".join([suggest_alter_table_add_columns_sql(table, missing) for table, missing in self.corrections])
        if not sql:
            await interaction.followup.send("Rien à appliquer.", ephemeral=True)
            return
        try:
            res = supabase.rpc(ADMIN_SQL_EXEC_RPC, {"p_sql": sql}).execute()
            data, err = _parse_result(res)
            await interaction.followup.send(f"{'✅ SQL appliqué' if not err else f'❌ Erreur: {err}'}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Impossible d'exécuter automatiquement : {e}", ephemeral=True)

# ──────────────────────────────────────────────────────────────
# 🧠 COG PRINCIPAL
# ──────────────────────────────────────────────────────────────
class FixTables(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _scan_and_report(self, channel: discord.abc.Messageable):
        try:
            expected = discover_expected_tables()
            if not expected:
                await safe_send(channel, "❌ Aucune utilisation de `supabase.table(...)` détectée.")
                return

            embed = discord.Embed(title="🔎 Rapport fixtables",
                                  description="Comparaison code ←→ Supabase", color=discord.Color.blurple())

            missing_tables = []
            corrections: List[Tuple[str, Set[str]]] = []
            type_mismatches: List[Tuple[str,str,str]] = []

            for table, info in expected.items():
                expected_cols = set(info.get("columns", {}).keys())
                actual_cols, actual_types, error = fetch_actual_columns(table)

                if actual_cols is None:
                    missing_tables.append(table)
                    embed.add_field(name=f"❌ {table}", value=f"Colonnes attendues: {expected_cols}\nErreur: {error}", inline=False)
                    continue

                missing = expected_cols - actual_cols
                extra = actual_cols - expected_cols

                # Type mismatch
                if actual_types:
                    for col in expected_cols & actual_cols:
                        etype = _infer_sql_type(col)
                        atype = actual_types.get(col)
                        if atype and etype.split()[0] not in atype:
                            type_mismatches.append((table,col,etype))

                if not missing and not extra and not type_mismatches:
                    embed.add_field(name=f"✅ {table}", value="Structure conforme", inline=False)
                else:
                    parts = []
                    if missing:
                        corrections.append((table, missing))
                        parts.append(f"Colonnes manquantes: {missing}")
                    if extra:
                        parts.append(f"Colonnes supplémentaires: {extra}")
                    if type_mismatches:
                        parts.append(f"Incompatibilité type: {type_mismatches}")
                    embed.add_field(name=f"⚠️ {table}", value="\n".join(map(str,parts)), inline=False)

            view = FixTablesView(missing_tables, corrections, type_mismatches) if (missing_tables or corrections or type_mismatches) else None
            await safe_send(channel, embed=embed, view=view)
        except Exception as e:
            await safe_send(channel, f"❌ Erreur lors de l'analyse:\n{traceback.format_exc()}")

    @app_commands.command(name="fixtables", description="🔧 Analyse & modifications SQL Supabase")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_fixtables(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self._scan_and_report(interaction.channel)

    @commands.command(name="fixtables")
    @commands.has_permissions(administrator=True)
    async def prefix_fixtables(self, ctx: commands.Context):
        await self._scan_and_report(ctx.channel)

# ──────────────────────────────────────────────────────────────
# FIN
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 🔌 Setup
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = FixTables(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)

