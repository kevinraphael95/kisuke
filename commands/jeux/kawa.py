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
from discord.ext import commands
from discord import app_commands
import random
import time
import inspect
from utils import kawashima_games
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Nom de table
# ────────────────────────────────────────────────────────────────────────────────
TABLE_NAME = "kawashima_scores"

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Kawashima(commands.Cog):
    """Mode arcade — Entraînement cérébral avec classement global."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.minijeux = []
        for name, func in inspect.getmembers(kawashima_games, inspect.iscoroutinefunction):
            if not name.startswith("_"):
                emoji = getattr(func, "emoji", "🎮")
                titre = getattr(func, "title", func.__name__.replace("_", " ").title())
                self.minijeux.append((f"{emoji} {titre}", func))

    # ───────────────────────────────────────────────────────────────────────
    # 🎮 Commande principale
    # ───────────────────────────────────────────────────────────────────────
    @commands.command(name="kawashima", aliases=["k"], help="Lance le mode arcade ou affiche le top 20.")
    async def kawashima_cmd(self, ctx: commands.Context, arg: str = ""):
        if arg.lower() == "top":
            await self.show_leaderboard(ctx)
        else:
            await self.run_arcade(ctx)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────    
    @app_commands.command(name="kawashima", description="Mode arcade Kawashima ou Top 20.")
    async def kawashima_slash(self, interaction: discord.Interaction, arg: str = ""):
        if arg.lower() == "top":
            await self.show_leaderboard(interaction)
        else:
            await self.run_arcade(interaction)

    # ───────────────────────────────────────────────────────────────────────
    # 🧩 Fonction mode arcade
    # ───────────────────────────────────────────────────────────────────────
    async def run_arcade(self, ctx_or_interaction):
        embed = discord.Embed(
            title="🧠 Entraînement cérébral — Mode Arcade",
            description="Réponds vite à chaque mini-jeu !",
            color=discord.Color.blurple(),
        )

        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed)
            message = await ctx_or_interaction.original_response()
            user = ctx_or_interaction.user
        else:
            message = await ctx_or_interaction.send(embed=embed)
            user = ctx_or_interaction.author

        get_user_id = lambda: user.id
        random.shuffle(self.minijeux)
        total_score = 0
        results = []

        for index, (name, game) in enumerate(self.minijeux, start=1):
            start = time.time()
            success = await game(message, embed, get_user_id, self.bot)
            end = time.time()
            elapsed = round(end - start, 2)
            score = (1000 + max(0, 500 - int(elapsed * 25))) if success else 0
            total_score += score
            results.append((index, name, success, elapsed, score))

        results_text = "\n".join(
            f"**Jeu {i}** {'✅' if s else '❌'} {name}{f' - {t}s' if s else ''}"
            for i, name, s, t, _ in results
        )

        if total_score >= 5000:
            rank = "🧠 Génie cérébral"
        elif total_score >= 3500:
            rank = "🤓 Bonne forme mentale"
        elif total_score >= 2000:
            rank = "🙂 Correct"
        else:
            rank = "😴 En veille..."

        # Enregistrement Supabase
        try:
            supabase.table(TABLE_NAME).insert({
                "user_id": str(user.id),
                "username": str(user.name),
                "score": total_score,
                "timestamp": int(time.time())
            }).execute()
        except Exception as e:
            print(f"[Kawashima] Erreur insertion Supabase: {e}")

        # Récupération leaderboard Top 20
        try:
            leaderboard = (
                supabase.table(TABLE_NAME)
                .select("username, score")
                .order("score", desc=True)
                .limit(20)
                .execute()
            )
            entries = leaderboard.data if leaderboard and leaderboard.data else []
            top_text = "\n".join(
                f"**{i+1}.** {entry['username']} — `{entry['score']:,}` pts"
                for i, entry in enumerate(entries)
            ) or "*Aucun score enregistré pour le moment*"
        except Exception as e:
            top_text = f"⚠️ Erreur récupération classement : {e}"

        embed.clear_fields()
        embed.title = "🏁 Résultats — Mode Arcade"
        embed.description = (
            f"**Résultats**\n{results_text}\n\n"
            f"**Score total :** `{total_score:,}` pts\n"
            f"**Niveau cérébral :** {rank}\n\n"
            f"🏆 **Classement Global (Top 20)**\n{top_text}"
        )
        embed.color = discord.Color.gold()
        await message.edit(embed=embed)

    # ───────────────────────────────────────────────────────────────────────
    # 🧩 Fonction affichage Top 20
    # ───────────────────────────────────────────────────────────────────────
    async def show_leaderboard(self, ctx_or_interaction):
        embed = discord.Embed(
            title="🏆 Kawashima — Top 20",
            description="Voici le classement global des meilleurs scores !",
            color=discord.Color.gold()
        )

        try:
            leaderboard = (
                supabase.table(TABLE_NAME)
                .select("username, score")
                .order("score", desc=True)
                .limit(20)
                .execute()
            )
            entries = leaderboard.data if leaderboard and leaderboard.data else []
            top_text = "\n".join(
                f"**{i+1}.** {entry['username']} — `{entry['score']:,}` pts"
                for i, entry in enumerate(entries)
            ) or "*Aucun score enregistré pour le moment*"
        except Exception as e:
            top_text = f"⚠️ Erreur récupération classement : {e}"

        embed.add_field(name="Top 20", value=top_text, inline=False)

        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed)
        else:
            await ctx_or_interaction.send(embed=embed)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Kawashima(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)


