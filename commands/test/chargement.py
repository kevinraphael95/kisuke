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

    def make_bar(self, progress: float, total: int, style: int) -> str:
        """
        Génère une barre de chargement en fonction du style choisi.
        """
        styles = {
            1: ("🟦", "⬜"),  # Classique
            2: ("█", "░"),   # Terminal
            3: ("🔵", "⚪"),  # Bulles
            4: ("🧱", "⬛"),  # Briques
        }
        filled_char, empty_char = styles.get(style, styles[1])

        if style == 2:
            percent = min(int(progress), 100)
            bar_length = 25
            filled_length = int((percent / 100) * bar_length)
            bar = filled_char * filled_length + empty_char * (bar_length - filled_length)
            return f"[{bar}] {percent}%"
        else:
            current_blocks = int((progress / 100) * total)
            bar = filled_char * current_blocks + empty_char * (total - current_blocks)
            return f"|{bar}| {int(progress)}%"

    @commands.command(
        name="chargement",
        aliases=["load"],
        help="Affiche une barre de chargement stylisée.",
        description="Simule un chargement avec une barre animée (styles : 1 à 4)."
    )
    async def chargement(self, ctx: commands.Context, style: int = 1):
        """
        Commande principale qui simule une barre de chargement stylisée.
        L'utilisateur peut choisir un style avec !chargement <style>.
        """
        try:
            await ctx.message.delete()  # 🔴 Supprime le message de commande
        except discord.Forbidden:
            pass  # Si le bot ne peut pas supprimer

        style = max(1, min(style, 4))  # 🔒 Sécurise le style (entre 1 et 4)
        message = await ctx.send(f"🔄 Chargement en cours...\n{self.make_bar(0, 20, style)}")

        if style == 2:
            progress = 0
            while progress < 100:
                await asyncio.sleep(random.uniform(0.2, 0.4))
                progress += random.randint(1, 5)
                progress = min(progress, 100)
                await message.edit(content=f"🔄 Chargement en cours...\n{self.make_bar(progress, 20, style)}")
        else:
            total_steps = 20
            progress = 0
            while progress < total_steps:
                await asyncio.sleep(random.uniform(0.2, 0.4))
                progress += 1
                await message.edit(content=f"🔄 Chargement en cours...\n{self.make_bar((progress / total_steps) * 100, total_steps, style)}")

        await message.edit(content=f"✅ Chargement terminé !\n{self.make_bar(100, 20, style)}")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Chargement(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
