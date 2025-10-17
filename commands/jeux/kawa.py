# ────────────────────────────────────────────────────────────────────────────────
# 📌 kawashima.py — Commande /kawashima et !kawashima
# Objectif : Lancer tous les mini-jeux style Professeur Kawashima
# Catégorie : Autre
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from utils.kawashima_games import *

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Kawashima(commands.Cog):
    """
    Commande /kawashima et !kawashima — Lance tous les mini-jeux d'entraînement cérébral
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.minijeux = [
            calcul_rapide,
            memoire_numerique,
            trouver_intrus,
            trouver_difference,
            suite_logique,
            typo_trap
        ]

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="kawashima",
        description="Lance tous les mini-jeux d'entraînement cérébral !"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_kawashima(self, interaction: discord.Interaction):
        await self.run_all(interaction)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="kawashima",
        aliases=["k"],
        help="Lance tous les mini-jeux d'entraînement cérébral !"
    )
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_kawashima(self, ctx: commands.Context):
        await self.run_all(ctx)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction pour lancer tous les mini-jeux
    # ────────────────────────────────────────────────────────────────────────────
    async def run_all(self, ctx_or_interaction):
        embed = discord.Embed(
            title="🧠 Entraînement cérébral Kawashima",
            description="Réponds aux mini-jeux suivants dans l'ordre !",
            color=0x00ff00
        )
        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed)
        else:
            await ctx_or_interaction.send(embed=embed)

        send = lambda text: ctx_or_interaction.followup.send(text) if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.send(text)
        get_user_id = lambda: ctx_or_interaction.user.id if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.author.id

        games = self.minijeux.copy()
        random.shuffle(games)
        for game in games:
            await game(ctx_or_interaction, send, get_user_id, self.bot)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Kawashima(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Autre"
    await bot.add_cog(cog)
