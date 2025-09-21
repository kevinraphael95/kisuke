# ────────────────────────────────────────────────────────────────────────────────
# 📌 fixtables.py — Commande admin /fixtables et !fixtables
# Objectif : Scanne le code pour trouver les tables Supabase utilisées et les recrée si absentes
# Catégorie : Admin
# Accès : Admin uniquement
# Cooldown : 1 utilisation / 30 secondes / serveur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import os
import re
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🔍 Fonction utilitaire — Scan du code pour trouver les tables utilisées
# ────────────────────────────────────────────────────────────────────────────────
def discover_tables(commands_dir="commands"):
    """
    Scanne récursivement le dossier `commands/` et extrait toutes les occurrences de
    supabase.table("xxx") pour détecter les noms de tables utilisés.
    """
    table_pattern = re.compile(r'supabase\.table\(["\']([\w\d_]+)["\']\)')
    found_tables = set()

    for root, _, files in os.walk(commands_dir):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    code = f.read()
                    matches = table_pattern.findall(code)
                    found_tables.update(matches)

    return sorted(found_tables)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class FixTables(commands.Cog):
    """Commande /fixtables et !fixtables — Scanne le code et recrée les tables manquantes"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _scan_and_fix(self, channel: discord.abc.Messageable):
        tables = discover_tables()
        if not tables:
            await safe_send(channel, "❌ Aucune table Supabase détectée dans les commandes.")
            return

        report_lines = []
        for table in tables:
            try:
                # Test simple pour voir si la table existe
                supabase.table(table).select("*").limit(1).execute()
                report_lines.append(f"✅ **{table}** : Table existante")
            except Exception:
                report_lines.append(f"⚠️ **{table}** : Table manquante → création...")
                try:
                    # Création minimale (clé id + timestamp)
                    create_sql = (
                        f"CREATE TABLE IF NOT EXISTS public.{table} ("
                        f"id uuid PRIMARY KEY DEFAULT gen_random_uuid(), "
                        f"created_at timestamp with time zone NOT NULL DEFAULT now()"
                        ");"
                    )
                    supabase.rpc("exec_sql", {"sql": create_sql}).execute()
                    report_lines.append(f"✅ Table **{table}** créée avec succès.")
                except Exception as e:
                    report_lines.append(f"❌ Erreur création de {table} : `{e}`")

        embed = discord.Embed(
            title="🔧 Scan & Fix des Tables Supabase",
            description="\n".join(report_lines),
            color=discord.Color.orange()
        )
        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="fixtables", description="🔧 Scanne le code et recrée les tables Supabase manquantes")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: (i.guild_id or i.user.id))
    async def slash_fixtables(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self._scan_and_fix(interaction.channel)
        await interaction.followup.send("✅ Vérification terminée !", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="fixtables")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 30.0, commands.BucketType.guild)
    async def prefix_fixtables(self, ctx: commands.Context):
        await self._scan_and_fix(ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = FixTables(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
