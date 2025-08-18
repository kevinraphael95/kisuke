# ────────────────────────────────────────────────────────────────────────────────
# 📌 test_taches.py — Commande interactive /testtache et !testtache
# Objectif : Tester toutes les tâches interactives du mode Hollow Among Us (Bleach)
# Catégorie : Mini-jeux / Tests
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands

from utils.taches import NOM_TACHES, lancer_tache_unique
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class TestTache(commands.Cog):
    """
    Commande /testtache et !testtache — Tester une tâche interactive spécifique
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _lancer_tache(self, destination, nom_tache: str):
        """Lance une tâche spécifique sur ctx ou interaction."""
        nom_tache = nom_tache.lower()
        if nom_tache not in NOM_TACHES:
            msg = f"❌ Tâche inconnue : `{nom_tache}`\nTâches dispo : {', '.join(NOM_TACHES.keys())}"
            if isinstance(destination, discord.Interaction):
                await safe_respond(destination, msg, ephemeral=True)
            else:
                await safe_send(destination, msg)
            return
        await lancer_tache_unique(destination, nom_tache)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="testtache", description="Tester une tâche interactive spécifique")
    @app_commands.describe(tache="Nom de la tâche à tester")
    async def slash_testtache(self, interaction: discord.Interaction, tache: str):
        """Commande slash qui lance une tâche."""
        try:
            await interaction.response.defer()
            await self._lancer_tache(interaction, tache)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /testtache] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue lors du lancement de la tâche.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="testtache")
    async def prefix_testtache(self, ctx: commands.Context, nom_tache: str):
        """Commande préfixe qui lance une tâche."""
        try:
            await self._lancer_tache(ctx, nom_tache)
        except Exception as e:
            print(f"[ERREUR !testtache] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors du lancement de la tâche.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TestTache(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
