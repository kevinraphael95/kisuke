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
import asyncio
from utils import kawashima_games
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# Table
# ────────────────────────────────────────────────────────────────────────────────
TABLE_NAME = "kawashima_scores"

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Fonction utilitaire : attente de réponse préfixée
# ────────────────────────────────────────────────────────────────────────────────
async def wait_for_prefixed_answer(bot, channel, user_id, timeout=10):
    """Attend un message commençant par '!' de l'utilisateur donné et le supprime ensuite."""
    def check(msg):
        return (
            msg.author.id == user_id
            and msg.channel == channel
            and msg.content.startswith("!")
        )

    try:
        msg = await bot.wait_for("message", timeout=timeout, check=check)
        content = msg.content[1:].strip()  # retire le "!"
        await msg.delete(delay=0.3)
        return content
    except asyncio.TimeoutError:
        return None

# ────────────────────────────────────────────────────────────────────────────────
# Commande principale
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

    # ────────────────────────────────────────────────────────────────────────
    # Commande textuelle et slash
    # ────────────────────────────────────────────────────────────────────────
    @commands.command(name="entrainement_cerebral", aliases=["ec", "kawashima", "k"], help="Entraînement cérébral.")
    async def kawashima_cmd(self, ctx: commands.Context, arg: str = ""):
        if arg.lower() == "top":
            await self.show_leaderboard(ctx)
        else:
            await self.run_arcade(ctx)

    @app_commands.command(name="entrainement_cerebral", description="Entraînement cérébral.")
    async def kawashima_slash(self, interaction: discord.Interaction, arg: str = ""):
        if arg.lower() == "top":
            await self.show_leaderboard(interaction)
        else:
            await self.run_arcade(interaction)

    # ────────────────────────────────────────────────────────────────────────
    # Mode Arcade
    # ────────────────────────────────────────────────────────────────────────
    async def run_arcade(self, ctx_or_interaction):
        embed = discord.Embed(
            title="🧠 Entraînement cérébral.",
            description="Réponds vite à chaque mini-jeu (commence chaque réponse par `!`)\n\nExemple : `!42` ou `!bleu`",
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
        # Sélectionne 5 mini-jeux aléatoires
        selected_games = random.sample(self.minijeux, k=min(5, len(self.minijeux)))

        total_score = 0
        results = []

        for index, (name, game) in enumerate(selected_games, start=1):
            embed.color = discord.Color.blurple()
            embed.set_footer(text=f"Mini-jeu {index}/5 — Réponds avec !")
            await message.edit(embed=embed)

            start = time.time()
            # Chaque mini-jeu reçoit la fonction d’attente spéciale
            success = await game(message, embed, get_user_id, self.bot, wait_for_prefixed_answer)
            end = time.time()

            elapsed = round(end - start, 2)
            score = (1000 + max(0, 500 - int(elapsed * 25))) if success else 0
            total_score += score
            results.append((index, name, success, elapsed, score))

        # Résumé des résultats
        results_text = "\n".join(
            f"**Jeu {i}** {'✅' if s else '❌'} {name}{f' - {t}s' if s else ''}"
            for i, name, s, t, _ in results
        )

        # Rang mental
        if total_score >= 5000:
            rank = "🧠 Génie cérébral"
        elif total_score >= 3500:
            rank = "🤓 Bonne forme mentale"
        elif total_score >= 2000:
            rank = "🙂 Correct"
        else:
            rank = "😴 En veille..."

        # ─────────── Gestion Top 10 ───────────
        try:
            leaderboard = (
                supabase.table(TABLE_NAME)
                .select("id, score")
                .order("score", desc=True)
                .limit(10)
                .execute()
            )
            entries = leaderboard.data if leaderboard and leaderboard.data else []
            top_scores = [entry["score"] for entry in entries]

            if len(top_scores) < 10 or total_score > top_scores[-1]:
                supabase.table(TABLE_NAME).insert({
                    "user_id": str(user.id),
                    "username": str(user.name),
                    "score": total_score,
                    "timestamp": int(time.time())
                }).execute()

                # Nettoyage des scores en trop
                leaderboard_all = (
                    supabase.table(TABLE_NAME)
                    .select("id, score")
                    .order("score", desc=True)
                    .execute()
                )
                all_entries = leaderboard_all.data if leaderboard_all and leaderboard_all.data else []
                if len(all_entries) > 10:
                    lowest_ids = [e["id"] for e in sorted(all_entries, key=lambda x: x["score"])[:len(all_entries)-10]]
                    if lowest_ids:
                        supabase.table(TABLE_NAME).delete().in_("id", lowest_ids).execute()

        except Exception as e:
            print(f"[Kawashima] Erreur Top 10 Supabase: {e}")

        # ─────────── Classement global ───────────
        try:
            leaderboard = (
                supabase.table(TABLE_NAME)
                .select("username, score")
                .order("score", desc=True)
                .limit(10)
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
        embed.title = "Entraînement cérébral — 🏁 Résultats"
        embed.description = (
            f"**Résultats**\n{results_text}\n\n"
            f"**Score total :** `{total_score:,}` pts\n"
            f"**Niveau cérébral :** {rank}\n\n"
            f"🏆 **Classement Global (Top 10)**\n{top_text}"
        )
        embed.color = discord.Color.gold()
        embed.set_footer(text="Fin du mode Arcade 🧩")
        await message.edit(embed=embed)

    # ────────────────────────────────────────────────────────────────────────
    # Classement global (Top 10)
    # ────────────────────────────────────────────────────────────────────────
    async def show_leaderboard(self, ctx_or_interaction):
        embed = discord.Embed(
            title="🏆 Entraînement cérébral — Top 10",
            description="Voici le classement global des meilleurs scores !",
            color=discord.Color.gold()
        )

        try:
            leaderboard = (
                supabase.table(TABLE_NAME)
                .select("username, score")
                .order("score", desc=True)
                .limit(10)
                .execute()
            )
            entries = leaderboard.data if leaderboard and leaderboard.data else []
            top_text = "\n".join(
                f"**{i+1}.** {entry['username']} — `{entry['score']:,}` pts"
                for i, entry in enumerate(entries)
            ) or "*Aucun score enregistré pour le moment*"
        except Exception as e:
            top_text = f"⚠️ Erreur récupération classement : {e}"

        embed.add_field(name="Top 10", value=top_text, inline=False)

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
