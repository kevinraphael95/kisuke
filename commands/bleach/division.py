# ────────────────────────────────────────────────────────────────────────────────
# 📌 division.py — Commande interactive /division et !division
# Objectif : Déterminer ta division dans le Gotei 13 via un QCM avec réactions
# Catégorie : Bleach
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import asyncio
import random
from collections import Counter

from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "divisions_quiz.json")

def load_division_data():
    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {DATA_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Division(commands.Cog):
    """
    Commande /division et !division — Détermine ta division dans le Gotei 13
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _run_quiz(self, channel, author):
        data = load_division_data()
        if not data:
            await safe_send(channel, "❌ Données introuvables.")
            return

        all_questions = data["questions"]
        divisions = data["divisions"]
        personality_counter = Counter()

        # Tirer 10 questions aléatoires
        questions = random.sample(all_questions, k=10)

        def get_emoji(index):
            return ["🇦", "🇧", "🇨", "🇩"][index]

        q_index = 0
        message = None

        while q_index < len(questions):
            q = questions[q_index]

            # Choisir 4 réponses max parmi celles disponibles
            all_answers = list(q["answers"].items())
            selected_answers = random.sample(all_answers, min(4, len(all_answers)))

            desc = ""
            emojis = []
            for i, (answer, traits) in enumerate(selected_answers):
                emoji = get_emoji(i)
                desc += f"{emoji} {answer}\n"
                emojis.append((emoji, answer, traits))

            embed = discord.Embed(
                title=f"🧠 Test de division — Question {q_index + 1}/10",
                description=f"**{q['question']}**\n\n{desc}",
                color=discord.Color.orange()
            )

            if q_index == 0:
                message = await safe_send(channel, embed=embed)
            else:
                await safe_edit(message, embed=embed)

            # Ajouter les réactions pour les choix
            for emoji, _, _ in emojis:
                await message.add_reaction(emoji)

            def check(reaction, user):
                return (
                    user == author
                    and reaction.message.id == message.id
                    and str(reaction.emoji) in [e[0] for e in emojis]
                )

            try:
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                selected_emoji = str(reaction.emoji)
                selected_traits = next(traits for emoji, _, traits in emojis if emoji == selected_emoji)
                personality_counter.update(selected_traits)
            except asyncio.TimeoutError:
                await safe_send(channel, "⏱️ Temps écoulé. Test annulé.")
                return

            try:
                await message.clear_reactions()
            except discord.Forbidden:
                pass

            q_index += 1

        # Résultat final
        division_scores = {
            div: sum(personality_counter[trait] for trait in info["traits"])
            for div, info in divisions.items()
        }
        best_division = max(division_scores, key=division_scores.get)

        embed_result = discord.Embed(
            title="🧩 Résultat de ton test",
            description=f"Tu serais dans la **{best_division}** !",
            color=discord.Color.green()
        )
        embed_result.set_image(url=f"attachment://{os.path.basename(divisions[best_division]['image'])}")

        await safe_send(channel, embed=embed_result)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="division",
        description="Réponds à un QCM pour savoir dans quelle division du Gotei 13 tu serais."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_division(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._run_quiz(interaction.channel, interaction.user)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="division", help="Détermine ta division dans le Gotei 13")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_division(self, ctx: commands.Context):
        await self._run_quiz(ctx.channel, ctx.author)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Division(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
        
