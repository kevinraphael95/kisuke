# ────────────────────────────────────────────────────────────────────────────────
# 📌 kawashima.py — Commande /kawashima et !kawashima
# Objectif : Lancer tous les mini-jeux style Professeur Kawashima avec score arcade compact
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
import time
import inspect
from utils import kawashima_games

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Kawashima(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Auto-détection de tous les mini-jeux async dans kawashima_games
        self.minijeux = []
        for name, func in inspect.getmembers(kawashima_games, inspect.iscoroutinefunction):
            if not name.startswith("_"):  # ignore fonctions internes
                emoji = getattr(func, "emoji", "🎮")
                titre = getattr(func, "title", func.__name__.replace("_", " ").title())
                self.minijeux.append((f"{emoji} {titre}", func))

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="kawashima", description="Lance tous les mini-jeux cérébraux détectés automatiquement !")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_kawashima(self, interaction: discord.Interaction):
        await self.run_all(interaction)

    # 🔹 Commande PREFIX
    @commands.command(name="kawashima", aliases=["k"], help="Lance tous les mini-jeux cérébraux détectés automatiquement !")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_kawashima(self, ctx: commands.Context):
        await self.run_all(ctx)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction principale — Score arcade + résumé compact
    # ────────────────────────────────────────────────────────────────────────────
    async def run_all(self, ctx_or_interaction):
        embed = discord.Embed(
            title="🧠 Entraînement cérébral Kawashima",
            description="Réponds rapidement à chaque défi mental !",
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
            score = (1000 + max(0, 500 - int(elapsed * 25))) if success else 0
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
