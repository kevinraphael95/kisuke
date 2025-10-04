# ────────────────────────────────────────────────────────────────────────────────
# 📌 fixtables.py — Commande interactive /fixtables et !fixtables
# Objectif : Vérifier les tables et colonnes utilisées par le bot, comparer avec Supabase
#            et générer des suggestions SQL par table avec navigation par page.
# Catégorie : Admin
# Accès : Administrateurs uniquement
# Cooldown : 30 secondes par serveur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from typing import Dict, List, Tuple
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Config
# ────────────────────────────────────────────────────────────────────────────────
CODE_SCAN_DIRS = ["commands", "tasks"]
WINDOW_CHARS = 2500

# ────────────────────────────────────────────────────────────────────────────────
# 🔎 Helpers — Chargement tables déclarées
# ────────────────────────────────────────────────────────────────────────────────
def load_tables_from_file(path: str) -> Dict[str, Dict]:
    """
    Analyse le fichier Python et extrait la variable TABLES sans exécuter le reste du code.
    """
    tables: Dict[str, Dict] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        inside_tables = False
        table_lines = []

        for line in lines:
            stripped = line.strip()

            # Début de la section TABLES
            if stripped.startswith("TABLES") and "=" in stripped:
                inside_tables = True

            if inside_tables:
                table_lines.append(line)

                # Fin probable de la déclaration du dict
                if stripped == "}" or stripped.endswith("}"):
                    inside_tables = False
                    try:
                        code = "".join(table_lines)
                        local_vars = {}
                        exec(code, {}, local_vars)
                        if "TABLES" in local_vars and isinstance(local_vars["TABLES"], dict):
                            tables.update(local_vars["TABLES"])
                    except Exception as e:
                        print(f"[⚠️] Impossible de parser TABLES dans {path} : {e}")
                    table_lines = []

    except Exception as e:
        print(f"[⚠️] Erreur lecture fichier {path} : {e}")

    return tables


def discover_expected_tables(dirs: List[str] = CODE_SCAN_DIRS) -> Dict[str, Dict]:
    """
    Scanne les répertoires commands/ et tasks/ pour trouver les sections TABLES = {...}.
    """
    results: Dict[str, Dict] = {}
    for base_dir in dirs:
        for root, _, files in os.walk(base_dir):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(root, fn)
                tables = load_tables_from_file(path)
                for table_name, info in tables.items():
                    results[table_name] = {
                        "columns": {col: None for col in info.get("columns", {})},
                        "locations": [(path, 1)]
                    }
    return results


def _infer_sql_type(c: str) -> str:
    """Détecte un type SQL probable pour une colonne donnée."""
    c = c.lower()
    if c.endswith("_id") or c in {"user_id", "guild_id", "channel_id"}:
        return "text"
    if c.endswith("_at") or c.startswith("last_"):
        return "timestamp with time zone"
    if c in {"points", "spawn_delay", "quantity", "argent", "bonus5"}:
        return "integer"
    if c.startswith("is_") or c.startswith("has_") or c in {"active_skill", "en_attente"}:
        return "boolean"
    if c in {"inventory", "garden_grid", "potions"}:
        return "jsonb"
    return "text"

# ────────────────────────────────────────────────────────────────────────────────
# 🗄️ Récupération structure Supabase
# ────────────────────────────────────────────────────────────────────────────────
def fetch_actual_columns(table: str) -> Tuple[Dict[str, str], bool]:
    """Retourne (colonnes:types, existe:bool) depuis Supabase."""
    try:
        res = supabase.table(table).select("*").limit(1).execute()
        if not res or not getattr(res, "data", None):
            return {}, True
        row = res.data[0]
        return {k: str(type(v)) for k, v in row.items()}, True
    except Exception:
        return {}, False

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Pagination par table
# ────────────────────────────────────────────────────────────────────────────────
class TablePaginator(View):
    def __init__(self, pages: List[discord.Embed], sql_per_table: Dict[str, Tuple[str, str]]):
        super().__init__(timeout=180)
        self.pages = pages
        self.sql_per_table = sql_per_table
        self.index = 0
        self.message = None

    async def update_message(self, interaction=None):
        if interaction:
            await interaction.response.edit_message(embed=self.pages[self.index], view=self)
        elif self.message:
            await safe_edit(self.message, embed=self.pages[self.index], view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: Button):
        self.index = (self.index - 1) % len(self.pages)
        await self.update_message(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        self.index = (self.index + 1) % len(self.pages)
        await self.update_message(interaction)

    @discord.ui.button(label="Créer table", style=discord.ButtonStyle.success)
    async def create_table(self, interaction: discord.Interaction, button: Button):
        table = self.pages[self.index].title.split("`")[1]
        sql = self.sql_per_table.get(table, ("", ""))[0] or "-- Rien à créer"
        await interaction.response.send_message(f"```sql\n{sql}\n```", ephemeral=True)

    @discord.ui.button(label="Modifier table", style=discord.ButtonStyle.primary)
    async def alter_table(self, interaction: discord.Interaction, button: Button):
        table = self.pages[self.index].title.split("`")[1]
        sql = self.sql_per_table.get(table, ("", ""))[1] or "-- Rien à modifier"
        await interaction.response.send_message(f"```sql\n{sql}\n```", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class FixTables(commands.Cog):
    """
    /fixtables et !fixtables — Vérifie les tables Supabase et génère un rapport interactif paginé
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _scan_and_report(self, channel: discord.abc.Messageable):
        try:
            expected = discover_expected_tables()
            if not expected:
                await safe_send(channel, "❌ Aucune table détectée dans le code.")
                return

            pages = []
            sql_per_table = {}

            for table, info in expected.items():
                try:
                    expected_cols = {c: _infer_sql_type(c) for c in info["columns"].keys()}
                    actual_cols, exists = fetch_actual_columns(table)

                    embed = discord.Embed(title=f"📄 Table `{table}`", color=discord.Color.blurple())
                    embed.add_field(
                        name="📌 Colonnes attendues (code)",
                        value="\n".join(f"`{c}` → `{t}`" for c, t in expected_cols.items()) or "Aucune colonne détectée",
                        inline=False
                    )
                    embed.add_field(
                        name="🗄️ Colonnes réelles (Supabase)",
                        value="\n".join(f"`{c}` → `{t}`" for c, t in actual_cols.items()) if exists else "❌ Table inexistante",
                        inline=False
                    )

                    missing = [c for c in expected_cols if c not in actual_cols]
                    extra = [c for c in actual_cols if c not in expected_cols]
                    diff = []
                    if missing: diff.append(f"⚠️ Manquantes : {', '.join(missing)}")
                    if extra: diff.append(f"ℹ️ Supplémentaires : {', '.join(extra)}")
                    embed.add_field(name="🔎 Différences", value="\n".join(diff) or "✅ Structure conforme", inline=False)

                    file_lines: Dict[str, List[int]] = {}
                    for f, ln in info["locations"]:
                        file_lines.setdefault(f, []).append(ln)
                    loc_str = "\n".join(
                        f"{os.path.relpath(f)}({', '.join(map(str, sorted(lines)))})"
                        for f, lines in file_lines.items()
                    )
                    embed.add_field(name="📂 Fichiers utilisant cette table", value=loc_str or "Non trouvé", inline=False)

                    sql_per_table[table] = (
                        f"CREATE TABLE IF NOT EXISTS {table} (\n  " +
                        ",\n  ".join(f"{c} {expected_cols[c]}" for c in expected_cols) +
                        "\n);",
                        "\n".join(f"ALTER TABLE {table} ADD COLUMN {c} {expected_cols[c]};" for c in missing)
                    )

                    pages.append(embed)

                except Exception as e:
                    await safe_send(channel, f"❌ Erreur sur la table `{table}` : {e}")

            if pages:
                view = TablePaginator(pages, sql_per_table)
                view.message = await safe_send(channel, embed=pages[0], view=view)

        except Exception as e:
            await safe_send(channel, f"❌ Une erreur est survenue : {e}")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commandes (Slash + Préfixe regroupées)
    # ────────────────────────────────────────────────────────────────────────────
    async def _handle_command(self, channel):
        await self._scan_and_report(channel)

    @app_commands.command(name="fixtables", description="Vérifie les tables Supabase et génère des SQL complets pour création/modification.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: i.guild_id or i.user.id)
    async def slash_fixtables(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._handle_command(interaction.channel)
        await interaction.delete_original_response()

    @commands.command(name="fixtables", help="Vérifie les tables Supabase et génère des SQL complets pour création/modification.")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 30.0, commands.BucketType.guild)
    async def prefix_fixtables(self, ctx: commands.Context):
        await self._handle_command(ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = FixTables(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)

