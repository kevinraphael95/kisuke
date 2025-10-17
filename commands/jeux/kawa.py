# ────────────────────────────────────────────────────────────────────────────────
# 📌 kawashima.py — Commande /kawashima et !kawashima
# Objectif : Lancer tous les mini-jeux style Professeur Kawashima avec score final
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
from utils.kawashima_games import *

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Kawashima(commands.Cog):
    """
    Commande /kawashima et !kawashima — Lance tous les mini-jeux avec score final
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
        description="Lance tous les mini-jeux d'entraînement cérébral avec score !"
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
        help="Lance tous les mini-jeux d'entraînement cérébral avec score !"
    )
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_kawashima(self, ctx: commands.Context):
        await self.run_all(ctx)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction pour lancer tous les mini-jeux avec embed unique et score
    # ────────────────────────────────────────────────────────────────────────────
    async def run_all(self, ctx_or_interaction):
        embed = discord.Embed(
            title="🧠 Entraînement cérébral Kawashima",
            description="Réponds aux mini-jeux suivants !",
            color=0x00ff00
        )

        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed)
            ctx = await ctx_or_interaction.original_response()
        else:
            ctx = ctx_or_interaction

        get_user_id = lambda: ctx_or_interaction.user.id if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.author.id

        score = 0
        games = self.minijeux.copy()
        random.shuffle(games)

        for game in games:
            result = await game(ctx, embed, get_user_id, self.bot)
            if result:
                score += 1

        embed.clear_fields()
        embed.add_field(name="🏆 Score final", value=f"{score} / {len(games)}", inline=False)
        embed.color = 0xffd700
        await ctx.edit(embed=embed)



# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Kawashima(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Autre"
    await bot.add_cog(cog)
