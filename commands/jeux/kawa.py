# ────────────────────────────────────────────────────────────────────────────────
# 📌 kawashima.py — Commande /kawashima et !kawashima
# Objectif : Lancer tous les mini-jeux style Professeur Kawashima avec score arcade compact
# Catégorie : Autre
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import random
import time
from utils.kawashima_games import *

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Kawashima(commands.Cog):
    """
    Commande /kawashima et !kawashima — Mini-jeux d'entraînement cérébral avec score compact
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.minijeux = [
            ("🧮 Calcul rapide", calcul_rapide),
            ("🔢 Mémoire numérique", memoire_numerique),
            ("🔍 Trouver l’intrus", trouver_intrus),
            ("🔎 Trouver la différence", trouver_difference),
            ("➗ Suite logique", suite_logique),
            ("✏️ Typo trap", typo_trap)
        ]

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="kawashima",
        description="Lance tous les mini-jeux d'entraînement cérébral avec score arcade compact !"
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
        help="Lance tous les mini-jeux d'entraînement cérébral avec score arcade compact !"
    )
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_kawashima(self, ctx: commands.Context):
        await self.run_all(ctx)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction principale — Score compact + arcade
    # ────────────────────────────────────────────────────────────────────────────
    async def run_all(self, ctx_or_interaction):
        embed = discord.Embed(
            title="🧠 Entraînement cérébral Kawashima",
            description="Prépare-toi à relever plusieurs défis mentaux !",
            color=0x00ff00
        )

        # Envoi initial
        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed)
            message = await ctx_or_interaction.original_response()
            user_id = ctx_or_interaction.user.id
        else:
            message = await ctx_or_interaction.send(embed=embed)
            user_id = ctx_or_interaction.author.id

        get_user_id = lambda: user_id

        random.shuffle(self.minijeux)
        total_score = 0
        results_text = ""
        results = []

        # ─────────── Boucle sur les mini-jeux ───────────
        for index, (name, game) in enumerate(self.minijeux, start=1):
            start = time.time()
            success = await game(message, embed, get_user_id, self.bot)
            end = time.time()
            elapsed = round(end - start, 2)

            # Score arcade
            if success:
                base = 1000
                speed_bonus = max(0, 500 - int(elapsed * 25))
                score = base + speed_bonus
            else:
                score = 0

            total_score += score
            results.append((index, name, success, elapsed, score))

        # ─────────── Génération du texte compact ───────────
        for i, name, success, elapsed, score in results:
            emoji = "✅" if success else "❌"
            temps = f" - {elapsed}s" if success else ""
            results_text += f"**Jeu {i}** {emoji} {name}{temps}\n"

        # ─────────── Score final + niveau ───────────
        if total_score >= 5000:
            rank = "🧠 Génie cérébral"
        elif total_score >= 3500:
            rank = "🤓 Bonne forme mentale"
        elif total_score >= 2000:
            rank = "🙂 Correct"
        else:
            rank = "😴 En veille..."

        embed.clear_fields()
        embed.title = "🏁 Résultats Kawashima"
        embed.description = (
            f"**Résultats**\n{results_text}\n"
            f"**Score total :** `{total_score:,}` pts\n"
            f"**Niveau cérébral :** {rank}"
        )
        embed.color = 0xffd700

        await message.edit(embed=embed)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Kawashima(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Autre"
    await bot.add_cog(cog)
