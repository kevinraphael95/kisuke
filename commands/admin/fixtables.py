# ────────────────────────────────────────────────────────────────────────────────
# 📌 fixtables.py — Commande admin /fixtables et !fixtables
# Objectif : Vérifie les tables Supabase utilisées par le bot et signale les différences
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
import json
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🔍 Fonctions utilitaires — Découverte & analyse
# ────────────────────────────────────────────────────────────────────────────────
def discover_expected_tables(commands_dir="commands"):
    """
    Scanne récursivement le code pour détecter :
    - Les noms de tables utilisés (supabase.table("xxx"))
    - Les colonnes attendues (select("col1, col2"), eq("col", ...), update({col: ...}))
    Retourne un dict : {table_name: {"expected_columns": set([...])}}
    """
    table_pattern = re.compile(r'supabase\.table\(["\']([\w\d_]+)["\']\)')
    select_pattern = re.compile(r'\.select\(["\']([^"\']+)["\']\)')
    eq_pattern = re.compile(r'\.eq\(["\']([^"\']+)["\']')
    update_pattern = re.compile(r'\.update\(\{([^}]+)\}')

    results = {}

    for root, _, files in os.walk(commands_dir):
        for file in files:
            if not file.endswith(".py"):
                continue
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                code = f.read()
                tables = table_pattern.findall(code)
                for table in tables:
                    if table not in results:
                        results[table] = {"expected_columns": set()}
                # Ajout des colonnes trouvées dans ce fichier
                for cols in select_pattern.findall(code):
                    for col in cols.split(","):
                        col = col.strip()
                        if "." not in col and len(tables) == 1:
                            results[tables[0]]["expected_columns"].add(col)
                for col in eq_pattern.findall(code):
                    if len(tables) == 1:
                        results[tables[0]]["expected_columns"].add(col)
                for update_block in update_pattern.findall(code):
                    for col_match in re.findall(r'["\'](\w+)["\']\s*:', update_block):
                        if len(tables) == 1:
                            results[tables[0]]["expected_columns"].add(col_match)

    return results

def fetch_actual_columns(table_name):
    """
    Récupère la structure réelle de la table via un select limit 1.
    Retourne un set de colonnes si possible, sinon None si table inexistante.
    """
    try:
        res = supabase.table(table_name).select("*").limit(1).execute()
        if not res.data:
            # Si pas de ligne → impossible de connaître toutes les colonnes, mais on a keys = []
            return set()
        return set(res.data[0].keys())
    except Exception:
        return None  # Table inexistante

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class FixTables(commands.Cog):
    """Commande /fixtables et !fixtables — Vérifie que les tables Supabase sont conformes"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _scan_and_report(self, channel: discord.abc.Messageable):
        expected = discover_expected_tables()
        if not expected:
            await safe_send(channel, "❌ Aucune table Supabase détectée dans les commandes.")
            return

        embed = discord.Embed(
            title="🔧 Vérification des tables Supabase",
            description="Analyse complète des tables utilisées par le bot",
            color=discord.Color.blurple()
        )

        for table, info in expected.items():
            expected_cols = info["expected_columns"]
            actual_cols = fetch_actual_columns(table)

            if actual_cols is None:
                embed.add_field(
                    name=f"❌ {table}",
                    value=f"Table inexistante.\n📌 Colonnes attendues : `{', '.join(sorted(expected_cols)) or 'Aucune détectée'}`",
                    inline=False
                )
            else:
                missing = expected_cols - actual_cols
                extra = actual_cols - expected_cols
                if not missing and not extra:
                    embed.add_field(
                        name=f"✅ {table}",
                        value="Structure conforme ✅",
                        inline=False
                    )
                else:
                    value_lines = []
                    if missing:
                        value_lines.append(f"⚠️ Colonnes manquantes : `{', '.join(sorted(missing))}`")
                    if extra:
                        value_lines.append(f"ℹ️ Colonnes supplémentaires : `{', '.join(sorted(extra))}`")
                    embed.add_field(
                        name=f"⚠️ {table}",
                        value="\n".join(value_lines),
                        inline=False
                    )

        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="fixtables", description="🔧 Vérifie la structure des tables Supabase")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: (i.guild_id or i.user.id))
    async def slash_fixtables(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self._scan_and_report(interaction.channel)
        await interaction.followup.send("✅ Vérification terminée !", ephemeral=True)

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
