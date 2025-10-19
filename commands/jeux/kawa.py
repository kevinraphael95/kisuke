# ────────────────────────────────────────────────────────────────────────────────
# 📌 kawashima.py — Commande /kawashima et !kawashima
# Objectif : Lancer 5 mini-jeux aléatoires style Professeur Kawashima avec score arcade
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
# Commande
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

    # ─────────── Commande texte ───────────
    @commands.command(name="kawashima", aliases=["k"], help="Lance le mode arcade ou affiche le top 10.")
    async def kawashima_cmd(self, ctx: commands.Context, arg: str = ""):
        if arg.lower() == "top":
            await self.show_leaderboard(ctx)
        else:
            await self.run_arcade(ctx)

    # ─────────── Commande slash ───────────
    @app_commands.command(name="kawashima", description="Mode arcade Kawashima ou Top 10.")
    async def kawashima_slash(self, interaction: discord.Interaction, arg: str = ""):
        if arg.lower() == "top":
            await self.show_leaderboard(interaction)
        else:
            await self.run_arcade(interaction)

    # ─────────── Lancement du mode arcade ───────────
    async def run_arcade(self, ctx_or_interaction):
        # Embed d’introduction
        start_embed = discord.Embed(
            title="🧠 Entraînement cérébral — Mode Arcade",
            description="Réponds vite à chaque mini-jeu !\n5 épreuves t’attendent...",
            color=discord.Color.blurple(),
        )

        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=start_embed)
            send = ctx_or_interaction.followup.send
            user = ctx_or_interaction.user
        else:
            await ctx_or_interaction.send(embed=start_embed)
            send = ctx_or_interaction.send
            user = ctx_or_interaction.author

        get_user_id = lambda: user.id
        total_score = 0
        results = []

        # ─────────── Sélection de 5 mini-jeux différents ───────────
        random.shuffle(self.minijeux)
        selected_games = self.minijeux[:5]

        for index, (name, game) in enumerate(selected_games, start=1):
            # Embed d’intro pour chaque mini-jeu
            intro_embed = discord.Embed(
                title=f"🧩 Mini-jeu {index} — {name}",
                description="Prépare-toi...",
                color=discord.Color.blurple()
            )
            await send(embed=intro_embed)
            await asyncio.sleep(1)

            # Exécution du mini-jeu
            start = time.time()
            success = await game(None, intro_embed, get_user_id, self.bot)
            end = time.time()
            elapsed = round(end - start, 2)
            score = (1000 + max(0, 500 - int(elapsed * 25))) if success else 0
            total_score += score
            results.append((index, name, success, elapsed, score))

            # Embed résultat pour ce mini-jeu
            result_embed = discord.Embed(
                title=f"🎯 Résultat — {name}",
                description=(
                    f"{'✅ Réussi' if success else '❌ Raté'}\n"
                    f"⏱️ Temps : `{elapsed}s`\n"
                    f"🏅 Score : `{score}` pts"
                ),
                color=discord.Color.green() if success else discord.Color.red()
            )
            await send(embed=result_embed)
            await asyncio.sleep(1)

        # ─────────── Calcul du rang ───────────
        results_text = "\n".join(
            f"**Jeu {i}** {'✅' if s else '❌'} {name}{f' — {t}s' if s else ''}"
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

        # ─────────── Gestion du Top 10 ───────────
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

        # ─────────── Récupération du Top 10 final ───────────
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

        # ─────────── Embed final ───────────
        final_embed = discord.Embed(
            title="🏁 Résultats — Mode Arcade",
            description=(
                f"**Résultats des 5 jeux :**\n{results_text}\n\n"
                f"**Score total :** `{total_score:,}` pts\n"
                f"**Niveau cérébral :** {rank}\n\n"
                f"🏆 **Classement Global (Top 10)**\n{top_text}"
            ),
            color=discord.Color.gold()
        )
        await send(embed=final_embed)

    # ─────────── Affichage du classement ───────────
    async def show_leaderboard(self, ctx_or_interaction):
        embed = discord.Embed(
            title="🏆 Kawashima — Top 10",
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
