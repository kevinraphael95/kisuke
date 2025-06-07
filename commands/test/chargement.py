# ────────────────────────────────────────────────────────────────────────────────
# 📌 chargement.py — Commande interactive !chargement
# Objectif : Afficher une barre de chargement stylisée et animée
# Catégorie : Test
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import asyncio
import random

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Chargement(commands.Cog):
    """
    Commande !chargement — Affiche une barre de chargement stylisée.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="chargement",
        aliases=["load"],
        help="Affiche une barre de chargement stylisée.",
        description="Simule un chargement avec une barre animée (stylisée 🟦⬜)."
    )
    async def chargement(self, ctx: commands.Context):
        """Commande principale qui simule une barre de chargement stylisée."""
        total_steps = 20
        progress = 0

        def make_bar(current: int, total: int) -> str:
            filled = "🟦" * current
            empty = "⬜" * (total - current)
            return f"[{filled}{empty}] {int((current/total)*100)}%"

        message = await ctx.send(f"🔄 Chargement en cours...\n{make_bar(progress, total_steps)}")

        while progress < total_steps:
            await asyncio.sleep(random.uniform(0.2, 0.5))  # entre 5 et 10s total
            progress += 1
            await message.edit(content=f"🔄 Chargement en cours...\n{make_bar(progress, total_steps)}")

        await message.edit(content=f"✅ Chargement terminé !\n{make_bar(progress, total_steps)}")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Chargement(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
