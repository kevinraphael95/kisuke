# ────────────────────────────────────────────────────────────────────────────────
# 📌 division.py — Commande interactive /division et !division
# Objectif : Déterminer la division qui te correspond via un QCM à choix boutons
# Catégorie : Bleach
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import json
import os
import random
from collections import Counter
import asyncio

from utils.discord_utils import safe_send, safe_edit, safe_respond  # ✅ Utils protégés

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "divisions_quiz.json")

def load_division_data():
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Vue pour une question
# ────────────────────────────────────────────────────────────────────────────────
class QuestionView(View):
    def __init__(self, bot, author, question, personality_counter, current_index, total_questions):
        super().__init__(timeout=60)
        self.bot = bot
        self.author = author
        self.question = question
        self.personality_counter = personality_counter
        self.current_index = current_index
        self.total_questions = total_questions
        self.message = None
        self.answered = asyncio.Event()

        # On limite à 4 réponses (tirées au hasard si +)
        answers = list(question["answers"].items())
        if len(answers) > 4:
            answers = random.sample(answers, k=4)

        emojis = ["🇦", "🇧", "🇨", "🇩"]

        for i, (answer_text, traits) in enumerate(answers):
            button = Button(
                label=f"{emojis[i]} {answer_text}",
                style=discord.ButtonStyle.secondary,
                custom_id=f"answer_{i}"
            )
            button.callback = self.make_callback(traits)
            self.add_item(button)

    def make_callback(self, traits):
        async def callback(interaction: discord.Interaction):
            if interaction.user != self.author:
                await safe_respond(interaction, "❌ Tu ne peux pas répondre à ce test.", ephemeral=True)
                return
            # Mise à jour des traits
            self.personality_counter.update(traits)
            # Désactivation des boutons
            for child in self.children:
                child.disabled = True
            await safe_edit(self.message, view=self)
            self.answered.set()
        return callback

    async def on_timeout(self):
        if not self.answered.is_set():
            for child in self.children:
                child.disabled = True
            if self.message:
                await safe_edit(self.message, view=self)
            self.answered.set()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Division(commands.Cog):
    """
    Commande /division et !division — Détermine ta division dans le Gotei 13.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _run_quiz(self, channel, author):
        data = load_division_data()
        all_questions = data["questions"]
        divisions = data["divisions"]
        personality_counter = Counter()

        # 10 questions aléatoires
        questions = random.sample(all_questions, k=10)

        for idx, q in enumerate(questions, start=1):
            embed = discord.Embed(
                title=f"🧠 Test de division — Question {idx}/10",
                description=f"**{q['question']}**",
                color=discord.Color.orange()
            )

            view = QuestionView(self.bot, author, q, personality_counter, idx, len(questions))
            if idx == 1:
                view.message = await safe_send(channel, embed=embed, view=view)
            else:
                view.message = await safe_edit(view.message, embed=embed, view=view)

            try:
                await asyncio.wait_for(view.answered.wait(), timeout=65)
            except asyncio.TimeoutError:
                await safe_send(channel, "⏱️ Temps écoulé. Test annulé.")
                return

        # Calcul des scores par division
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
        image_path = divisions[best_division].get("image")
        if image_path and os.path.exists(image_path):
            file = discord.File(image_path, filename=os.path.basename(image_path))
            embed_result.set_image(url=f"attachment://{os.path.basename(image_path)}")
            await safe_send(channel, embed=embed_result, file=file)
        else:
            await safe_send(channel, embed=embed_result)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="division", description="Détermine ta division dans le Gotei 13.")
    async def slash_division(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._run_quiz(interaction.channel, interaction.user)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /division] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue pendant le test.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="division", help="Détermine ta division dans le Gotei 13.")
    async def prefix_division(self, ctx: commands.Context):
        try:
            await self._run_quiz(ctx.channel, ctx.author)
        except Exception as e:
            print(f"[ERREUR !division] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue pendant le test.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Division(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
