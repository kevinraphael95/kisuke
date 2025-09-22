# ────────────────────────────────────────────────────────────────────────────────
# 📌 fixtables.py — Commande interactive /fixtables et !fixtables
# Objectif : Vérifier les tables/colonnes Supabase utilisées par le bot, comparer avec
#            la structure réelle, et générer des suggestions SQL (CREATE/ALTER)
# Catégorie : Admin
# Accès : Administrateurs uniquement
# Cooldown : 30 secondes par serveur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import os
import re
import traceback
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from typing import Dict, List, Set, Tuple

from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Config
# ────────────────────────────────────────────────────────────────────────────────
CODE_SCAN_DIR = "commands"
WINDOW_CHARS = 2500  # nombre de caractères à analyser après supabase.table(...)
SQL_SUGGESTION_MAX_COLS = 30

# ────────────────────────────────────────────────────────────────────────────────
# 🔎 Helpers — Détection tables et colonnes
# ────────────────────────────────────────────────────────────────────────────────
_table_re = re.compile(r'supabase\.table\(\s*["\']([\w\d_]+)["\']\s*\)')
_select_re = re.compile(r'\.select\(\s*["\']([^"\']+)["\']\s*\)')
_eq_re = re.compile(r'\.eq\(\s*["\']([\w\d_]+)["\']\s*,')
_update_dict_re = re.compile(r'\.(?:update|insert)\s*\(\s*\{([^}]+)\}', re.S)
_key_in_dict_re = re.compile(r'["\']([\w\d_]+)["\']\s*:')

def _infer_sql_type(column: str) -> str:
    """
    Déduit un type SQL plausible pour une colonne (heuristique simple).
    """
    c = column.lower()
    if c.endswith("_id") or c in {"user_id", "guild_id", "channel_id"}:
        return "text"
    if c in {"points", "spawn_delay", "quantity"}:
        return "integer"
    if c.endswith("_at") or c.startswith("last_"):
        return "timestamp with time zone"
    if c.startswith("is_") or c.startswith("has_"):
        return "boolean"
    return "text"

def discover_expected_tables(commands_dir: str = CODE_SCAN_DIR) -> Dict[str, Dict]:
    """
    Parcourt les fichiers .py pour trouver les tables et colonnes utilisées.
    Retourne un dict :
    {
        "table_name": {
            "columns": {"col": [(file, line), ...], ...},
            "locations": [(file, line), ...]
        }
    }
    """
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
                line_no = code[:match.start()].count("\n") + 1
                t_info = results.setdefault(table, {"columns": {}, "locations": []})
                t_info["locations"].append((path, line_no))

                window = code[match.end():match.end() + WINDOW_CHARS]

                # select(...)
                for s in _select_re.finditer(window):
                    cols = [c.strip() for c in s.group(1).split(",") if c.strip() != "*"]
                    for c in cols:
                        t_info["columns"].setdefault(c, []).append((path, line_no))

                # eq(...)
                for e in _eq_re.finditer(window):
                    c = e.group(1)
                    t_info["columns"].setdefault(c, []).append((path, line_no))

                # update/insert dict keys
                for block in _update_dict_re.finditer(window):
                    for k in _key_in_dict_re.findall(block.group(1)):
                        t_info["columns"].setdefault(k, []).append((path, line_no))
    return results

# ────────────────────────────────────────────────────────────────────────────────
# 🗄️ Lecture structure Supabase
# ────────────────────────────────────────────────────────────────────────────────
def fetch_actual_columns(table: str) -> Tuple[Set[str], Dict[str, str]]:
    """
    Retourne (colonnes, types) de la table depuis Supabase.
    (types = mapping col → type en texte)
    """
    try:
        res = supabase.table(table).select("*").limit(1).execute()
        if not res or not getattr(res, "data", None):
            return set(), {}
        row = res.data[0]
        return set(row.keys()), {k: str(type(v)) for k, v in row.items()}
    except Exception:
        return set(), {}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Boutons pour suggestions SQL
# ────────────────────────────────────────────────────────────────────────────────
class FixTablesView(View):
    def __init__(self, create_sql: str, add_sql: str, alter_sql: str):
        super().__init__(timeout=180)
        self.create_sql = create_sql
        self.add_sql = add_sql
        self.alter_sql = alter_sql

    @discord.ui.button(label="CREATE TABLE", style=discord.ButtonStyle.success)
    async def btn_create(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"```sql\n{self.create_sql or '-- Rien à créer'}\n```", ephemeral=True)

    @discord.ui.button(label="ALTER ADD COLUMNS", style=discord.ButtonStyle.primary)
    async def btn_add(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"```sql\n{self.add_sql or '-- Aucune colonne à ajouter'}\n```", ephemeral=True)

    @discord.ui.button(label="ALTER TYPES", style=discord.ButtonStyle.secondary)
    async def btn_alter(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(f"```sql\n{self.alter_sql or '-- Aucun type à modifier'}\n```", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal avec cooldown
# ────────────────────────────────────────────────────────────────────────────────
class FixTables(commands.Cog):
    """
    Commande /fixtables et !fixtables — Vérifie les tables Supabase et propose du SQL.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _scan_and_report(self, channel: discord.abc.Messageable):
        expected = discover_expected_tables(CODE_SCAN_DIR)

        embed = discord.Embed(
            title="🔎 Rapport fixtables",
            description="Comparaison entre tables attendues et Supabase.",
            color=discord.Color.blurple()
        )

        create_sql, add_sql, alter_sql = [], [], []

        for table, info in expected.items():
            expected_cols = set(info["columns"].keys())
            actual_cols, actual_types = fetch_actual_columns(table)

            if not actual_cols:
                embed.add_field(
                    name=f"❌ Table manquante : `{table}`",
                    value=f"Colonnes attendues : {', '.join(expected_cols) or 'aucune'}",
                    inline=False
                )
                create_sql.append(f"CREATE TABLE {table} ({', '.join(f'{c} {_infer_sql_type(c)}' for c in expected_cols)});")
                continue

            missing = expected_cols - actual_cols
            extra = actual_cols - expected_cols

            lines = []
            if missing:
                lines.append(f"⚠️ Colonnes manquantes : {', '.join(missing)}")
                add_sql.extend([f"ALTER TABLE {table} ADD COLUMN {c} {_infer_sql_type(c)};" for c in missing])
            if extra:
                lines.append(f"ℹ️ Colonnes supplémentaires : {', '.join(extra)}")

            embed.add_field(name=f"📄 {table}", value="\n".join(lines) or "✅ Structure conforme", inline=False)

        view = FixTablesView("\n".join(create_sql), "\n".join(add_sql), "\n".join(alter_sql))
        await safe_send(channel, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="fixtables", description="Vérifie les tables Supabase et génère des suggestions SQL.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: i.guild_id or i.user.id)
    async def slash_fixtables(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._scan_and_report(interaction.channel)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="fixtables")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 30.0, commands.BucketType.guild)
    async def prefix_fixtables(self, ctx: commands.Context):
        await self._scan_and_report(ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = FixTables(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
