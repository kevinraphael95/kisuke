# ────────────────────────────────────────────────────────────────────────────────
# 📌 test_taches.py — Commande interactive !testtache
# Objectif : Tester toutes les tâches interactives du mode Hollow Among Us (Bleach)
# Catégorie : Mini-jeux / Tests
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands

# Import depuis utils.taches
from utils.taches import NOM_TACHES, lancer_tache_unique

# Import utils Discord sécurisés
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Cog principal TestTache
# ────────────────────────────────────────────────────────────────────────────────
class TestTache(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 📌 Commande avec préfixe (!testtache)
    @commands.command(name="testtache")
    async def test_tache_prefix(self, ctx: commands.Context, nom_tache: str):
        """Tester une tâche spécifique en utilisant son nom."""
        nom_tache = nom_tache.lower()
        if nom_tache not in NOM_TACHES:
            await safe_send(
                ctx,
                f"❌ Tâche inconnue : `{nom_tache}`\nTâches dispo : {', '.join(NOM_TACHES.keys())}"
            )
            return
        await lancer_tache_unique(ctx, nom_tache)

    # 📌 Commande slash (/testtache)
    @app_commands.command(name="testtache", description="Tester une tâche interactive spécifique")
    @app_commands.describe(tache="Nom de la tâche à tester")
    async def test_tache_slash(self, interaction: discord.Interaction, tache: str):
        tache = tache.lower()
        if tache not in NOM_TACHES:
            await safe_respond(
                interaction,
                f"❌ Tâche inconnue : `{tache}`\nTâches dispo : {', '.join(NOM_TACHES.keys())}",
                ephemeral=True
            )
            return
        await lancer_tache_unique(interaction, tache)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TestTache(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
