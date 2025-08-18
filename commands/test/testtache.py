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

# Import commun : toutes les tâches et les vues
from utils.taches import TacheSelectView


# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Cog principal TestTache
# ────────────────────────────────────────────────────────────────────────────────
class TestTache(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 📌 Commande avec préfixe (!testtache)
    @commands.command(name="testtache")
    async def test_tache_prefix(self, ctx: commands.Context):
        """Tester les mini-jeux interactifs (version préfixe)."""
        view = TacheSelectView(self.bot)
        await ctx.send("🛠️ Choisis une tâche à tester dans le menu ci-dessous :", view=view)

    # 📌 Commande slash (/testtache)
    @app_commands.command(name="testtache", description="Tester les mini-jeux interactifs (version slash).")
    async def test_tache_slash(self, interaction: discord.Interaction):
        view = TacheSelectView(self.bot)
        await interaction.response.send_message("🛠️ Choisis une tâche à tester dans le menu ci-dessous :", view=view)




# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TestTache(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
