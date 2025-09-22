# ──────────────────────────────────────────────────────────────────────────────
# 📌 fixtables.py — Vérification & suggestions SQL pour Supabase
# ──────────────────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────
# 📦 Imports
# ──────────────────────────────────────────────────────────────────────────────
import os
import re
import traceback
import discord
from discord import app_commands
from discord.ext import commands
from typing import Dict, Set, List, Tuple, Optional
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ──────────────────────────────────────────────────────────────────────────────
# 🔧 Config
# ──────────────────────────────────────────────────────────────────────────────
CODE_SCAN_DIR = "commands"   # dossier à scanner
WINDOW_CHARS = 2500         # recherche locale autour du supabase.table(...) call
SQL_SUGGESTION_MAX_COLS = 30

# ──────────────────────────────────────────────────────────────────────────────
# 🔎 Helpers — parsing robust
# ──────────────────────────────────────────────────────────────────────────────
_table_re = re.compile(r'supabase\.table\(\s*["\']([\w\d_]+)["\']\s*\)')
_select_re = re.compile(r'\.select\(\s*["\']([^"\']+)["\']\s*\)')
_eq_re = re.compile(r'\.eq\(\s*["\']([\w\d_]+)["\']\s*,')
_update_dict_re = re.compile(r'\.(?:update|insert)\s*\(\s*\{([^}]+)\}', re.S)
_insert_dict_re = re.compile(r'\.insert\s*\(\s*\{([^}]+)\}', re.S)
_key_in_dict_re = re.compile(r'["\']([\w\d_]+)["\']\s*:')

def _infer_sql_type(column_name: str) -> str:
    """Heuristique simple pour proposer un type SQL."""
    cn = column_name.lower()
    if cn.endswith("_id") or cn in {"user_id", "guild_id", "channel_id", "message_id", "id_faux_reiatsu"}:
        return "text"
    if cn in {"points", "spawn_delay", "delay_minutes", "skill_cd", "spawn_message_id"}:
        return "integer"
    if cn.endswith("_at") or cn.startswith("last_") or cn in {"created_at", "last_spawn_at", "last_skill"}:
        return "timestamp with time zone"
    if cn.startswith("is_") or cn.startswith("has_") or cn in {"en_attente", "has_skill", "active"}:
        return "boolean"
    if "json" in cn or "data" in cn or cn in {"active_skill"}:
        return "jsonb"
    return "text"

def _parse_result(res):
    """Récupère data, error depuis l'objet supabase (dict ou res)."""
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

# ──────────────────────────────────────────────────────────────────────────────
# 🔍 Découverte des tables attendues
# ──────────────────────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────────────────────
# 🗄️ Lecture de la structure réelle (avec types)
# ──────────────────────────────────────────────────────────────────────────────
def fetch_actual_structure(table_name: str) -> Tuple[Optional[Dict[str, dict]], Optional[str]]:
    """
    Retourne {col: {"type": "...", "nullable": True/False}} ou None si erreur.
    """
    try:
        sql = f"""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = '{table_name}';
        """
        res = supabase.rpc("execute_sql", {"query": sql}).execute()
        data, err = _parse_result(res)
        if err:
            return None, str(err)
        if not data:
            return {}, None
        return {r["column_name"]: {
            "type": r["data_type"],
            "nullable": r["is_nullable"] == "YES"
        } for r in data}, None
    except Exception as e:
        return None, str(e)

# ──────────────────────────────────────────────────────────────────────────────
# 🧾 Génération SQL
# ──────────────────────────────────────────────────────────────────────────────
def suggest_create_table_sql(table: str, columns: Set[str]) -> str:
    if not columns:
        return f"-- CREATE TABLE {table} (...);"
    cols_lines = []
    for c in list(columns)[:SQL_SUGGESTION_MAX_COLS]:
        t = _infer_sql_type(c)
        cols_lines.append(f"  {c} {t}")
    body = ",\n".join(cols_lines)
    return f"CREATE TABLE IF NOT EXISTS {table} (\n{body}\n);"

def suggest_alter_table_add_columns_sql(table: str, missing: Set[str]) -> str:
    if not missing:
        return "-- Aucune colonne manquante."
    return "\n".join(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {c} {_infer_sql_type(c)};" for c in missing)

def suggest_alter_table_types_sql(table: str, mismatches: Dict[str, Tuple[str, str]]) -> str:
    if not mismatches:
        return "-- Aucun type différent."
    return "\n".join(
        f"-- {c}: {actual} → {expected}\nALTER TABLE {table} ALTER COLUMN {c} TYPE {expected} USING {c}::{expected};"
        for c, (expected, actual) in mismatches.items()
    )

# ──────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue interactive
# ──────────────────────────────────────────────────────────────────────────────
class FixTablesView(discord.ui.View):
    def __init__(self, missing_tables, corrections, type_mismatches):
        super().__init__(timeout=120)
        self.missing_tables = missing_tables
        self.corrections = corrections
        self.type_mismatches = type_mismatches

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator

    @discord.ui.button(label="Générer SQL (CREATE)", style=discord.ButtonStyle.success)
    async def _create_sql(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        blocks = [suggest_create_table_sql(t, set()) for t in self.missing_tables]
        await interaction.followup.send(f"```sql\n{'\n\n'.join(blocks)}\n```", ephemeral=True)

    @discord.ui.button(label="Générer SQL (ADD COLUMNS)", style=discord.ButtonStyle.primary)
    async def _alter_sql(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        parts = [suggest_alter_table_add_columns_sql(t, m) for t, m in self.corrections]
        await interaction.followup.send(f"```sql\n{'\n\n'.join(parts)}\n```", ephemeral=True)

    @discord.ui.button(label="Générer SQL (ALTER TYPES)", style=discord.ButtonStyle.secondary)
    async def _alter_types(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        parts = [suggest_alter_table_types_sql(t, m) for t, m in self.type_mismatches]
        await interaction.followup.send(f"```sql\n{'\n\n'.join(parts)}\n```", ephemeral=True)

# ──────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ──────────────────────────────────────────────────────────────────────────────
class FixTables(commands.Cog):
    """/fixtables & !fixtables — Analyse et suggestions SQL (colonnes + types)."""

    def __init__(self, bot):
        self.bot = bot

    async def _scan_and_report(self, channel, verbose=False):
        try:
            expected = discover_expected_tables(CODE_SCAN_DIR)
            if not expected:
                await safe_send(channel, "❌ Aucune utilisation de `supabase.table(...)` détectée.")
                return

            embed = discord.Embed(
                title="🔎 Rapport fixtables",
                description="Comparaison code ↔ Supabase (colonnes et types)",
                color=discord.Color.blurple()
            )

            missing_tables = []
            corrections = []
            type_mismatches = []

            for table, info in expected.items():
                expected_cols = set(info.get("columns", {}).keys())
                actual, error = fetch_actual_structure(table)

                if actual is None:
                    missing_tables.append(table)
                    embed.add_field(
                        name=f"❌ `{table}` absente",
                        value=f"Colonnes attendues : {', '.join(expected_cols) or 'Aucune'}",
                        inline=False
                    )
                    continue

                actual_cols = set(actual.keys())
                missing = expected_cols - actual_cols
                extra = actual_cols - expected_cols
                mismatches = {}

                for col in expected_cols & actual_cols:
                    expected_type = _infer_sql_type(col)
                    actual_type = actual[col]["type"]
                    if expected_type not in actual_type:  # comparaison simple
                        mismatches[col] = (expected_type, actual_type)

                if not missing and not extra and not mismatches:
                    embed.add_field(name=f"✅ `{table}`", value="Structure conforme ✅", inline=False)
                else:
                    lines = []
                    if missing:
                        corrections.append((table, missing))
                        lines.append(f"⚠️ Colonnes manquantes : {', '.join(sorted(missing))}")
                    if extra:
                        lines.append(f"ℹ️ Colonnes supplémentaires : {', '.join(sorted(extra))}")
                    if mismatches:
                        type_mismatches.append((table, mismatches))
                        diff = "\n".join([f"- {c}: {a} → {e}" for c, (e, a) in mismatches.items()])
                        lines.append(f"🔄 Types différents :\n{diff}")
                    embed.add_field(name=f"⚠️ `{table}`", value="\n".join(lines), inline=False)

            view = FixTablesView(missing_tables, corrections, type_mismatches) if (missing_tables or corrections or type_mismatches) else None
            await safe_send(channel, embed=embed, view=view)

        except Exception as e:
            tb = traceback.format_exc()
            print("[fixtables] ERREUR:", tb)
            await safe_send(channel, f"❌ Erreur :\n```py\n{tb[:1900]}\n```")

    @app_commands.command(name="fixtables", description="🔧 Analyse et suggestions SQL pour les tables Supabase")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_fixtables(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self._scan_and_report(interaction.channel, verbose=False)
        await interaction.followup.send("✅ Rapport généré.", ephemeral=True)

    @commands.command(name="fixtables")
    @commands.has_permissions(administrator=True)
    async def prefix_fixtables(self, ctx: commands.Context):
        await self._scan_and_report(ctx.channel, verbose=False)

# ──────────────────────────────────────────────────────────────────────────────
# 🔌 Setup
# ──────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = FixTables(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
        
