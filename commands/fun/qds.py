# ────────────────────────────────────────────────────────────────────────────────
# 📌 qds.py — Commande interactive !qds / !quizzdarksouls
# Objectif : QCM multijoueur sur Dark Souls, 5 questions par session quotidienne
# Catégorie : 🧠 Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands, tasks
import json
import os
import random
import datetime
from supabase import create_client
import asyncio


# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des questions depuis le fichier JSON
# ────────────────────────────────────────────────────────────────────────────────
QDS_JSON_PATH = os.path.join("data", "questions_dark_souls.json")

def load_questions():
    with open(QDS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🔐 Supabase configuration (à adapter avec variables d'env)
# ────────────────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Classe principale du Cog — QDS
# ────────────────────────────────────────────────────────────────────────────────
class QDS(commands.Cog):
    """
    🎯 Commande !qds — QCM multijoueur sur Dark Souls (5 questions)
    """

    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}  # Par serveur : session en cours

    def check_already_played(self, guild_id):
        today = datetime.datetime.utcnow().date().isoformat()
        response = supabase.table("qds_scores").select("date").eq("server_id", str(guild_id)).eq("date", today).execute()
        return len(response.data) > 0



    def save_score(self, guild_id, user_id, username, score):
        response = supabase.table("qds_scores") \
            .select("score") \
            .eq("server_id", str(guild_id)) \
            .eq("user_id", str(user_id)) \
            .execute()
    
        if response.data:
            current_score = response.data[0]["score"]
            new_score = current_score + score
            supabase.table("qds_scores") \
                .update({"score": new_score, "username": username}) \
                .eq("server_id", str(guild_id)) \
                .eq("user_id", str(user_id)) \
                .execute()
        else:
            supabase.table("qds_scores").insert({
                "server_id": str(guild_id),
                "user_id": str(user_id),
                "username": username,
                "score": score
            }).execute()







    

    @commands.command(name="qds", aliases=["quizzdarksouls"])
    async def qds(self, ctx):
        """Lance un quizz QCM multijoueur sur Dark Souls (5 questions)"""
        guild_id = ctx.guild.id

        intro_msg = await ctx.send(
            "🧠 **Ceci est un quizz sur Dark Souls !**\n"
            "Cliquez sur 🇯 pour rejoindre le quizz. Il faut au moins 2 joueurs.\n"
            "Répondez aux 5 questions à choix multiples en cliquant sur les réactions correspondantes."
        )
        await intro_msg.add_reaction("🇯")

        def join_check(reaction, user):
            return (
                reaction.message.id == intro_msg.id and
                str(reaction.emoji) == "🇯" and
                not user.bot
        )

        players = set()
        try:
            while len(players) < 2:
                reaction, user = await ctx.bot.wait_for("reaction_add", timeout=60.0, check=join_check)
                players.add(user.id)
        except asyncio.TimeoutError:
            return await ctx.send("⏳ Temps écoulé : il fallait au moins 2 joueurs pour commencer.")

        players_mentions = ", ".join(f"<@{pid}>" for pid in players)
        await ctx.send(f"✅ Joueurs prêts : {players_mentions}. Début du quizz !")




        data = load_questions()
        questions = (
            random.sample(data['facile'], 2) +
            random.sample(data['moyen'], 2) +
            random.sample(data['difficile'], 1)
        )
        random.shuffle(questions)

        scores = {}

        def check(reaction, user):
            return user != ctx.bot.user and str(reaction.emoji) in ["🇦", "🇧", "🇨", "🇩"]

        for i, q in enumerate(questions):
            embed = discord.Embed(
                title=f"❓ Question {i+1}/5",
                description=q['question'],
                color=discord.Color.dark_gold()
            )
            options = q['options']
            emojis = ["🇦", "🇧", "🇨", "🇩"]

            description = q['question'] + "\n\n"
            for em, opt in zip(emojis, options):
                description += f"{em} {opt}\n"

            embed = discord.Embed(
                title=f"❓ Question {i+1}/5",
                description=description,
                color=discord.Color.dark_gold()
            )
            embed.set_footer(text="Répondez en réagissant avec 🇦, 🇧, 🇨 ou 🇩 (30s)")


            msg = await ctx.send(embed=embed)
            for em in emojis:
                await msg.add_reaction(em)

            try:
                reactions = await ctx.bot.wait_for("reaction_add", timeout=30.0, check=check)
                for reaction, user in [reactions]:
                    if options[emojis.index(reaction.emoji)] == q['answer']:
                        scores[user.id] = scores.get(user.id, 0) + 1
            except:
                continue

        if not scores:
            return await ctx.send("❌ Aucun score enregistré. Pas de participants ?")

        leaderboard = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        lines = []
        for user_id, score in leaderboard:
            user = ctx.guild.get_member(user_id)
            if user:
                self.save_score(ctx.guild.id, user.id, user.name, score)
                lines.append(f"🏅 {user.mention} — {score}/5")

        await ctx.send("📊 Résultats du quizz :\n" + "\n".join(lines))

    @commands.command(name="classementqds")
    async def classement_qds(self, ctx):
        """Affiche le classement local QDS (Dark Souls)"""
        response = supabase.table("qds_scores").select("username", "score").eq("server_id", str(ctx.guild.id)).execute()
        if not response.data:
            return await ctx.send("❌ Aucun score enregistré pour ce serveur.")

        scores = {}
        for entry in response.data:
            scores[entry['username']] = scores.get(entry['username'], 0) + entry['score']

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        desc = "\n".join([f"🥇 {u} — {s} pts" for u, s in sorted_scores[:10]])
        embed = discord.Embed(title="🏆 Classement QDS", description=desc, color=discord.Color.gold())
        await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = QDS(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
