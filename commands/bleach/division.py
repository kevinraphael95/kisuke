# ────────────────────────────────────────────────────────────────────────────────
# 📌 division.py — Commande interactive !division et /division
# Objectif : Déterminer la division qui te correspond via un QCM interactif
# Catégorie : Bleach
# Accès : Tous
# Cooldown : 1 utilisation toutes les 5 secondes par utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
import json
import os
import random
from collections import Counter
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "divisions_quiz.json")

def load_division_data():
    """Charge le fichier JSON contenant les divisions et les questions."""
    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {DATA_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu de QCM interactif
# ────────────────────────────────────────────────────────────────────────────────
class QuestionSelect(Select):
    def __init__(self, parent_view, question, q_index):
        self.parent_view = parent_view
        self.question = question
        self.q_index = q_index

        # Tirer 4 réponses aléatoires parmi toutes les réponses possibles
        answers_items = list(question["answers"].items())
        if len(answers_items) > 4:
            answers_items = random.sample(answers_items, k=4)

        self.emoji_list = ["🇦", "🇧", "🇨", "🇩"]
        self.mapping = {self.emoji_list[i]: answers_items[i] for i in range(len(answers_items))}

        options = [
            discord.SelectOption(label=answer, value=emoji)
            for emoji, (answer, _) in self.mapping.items()
        ]
        super().__init__(placeholder="Choisis ta réponse", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_emoji = self.values[0]
        _, traits = self.mapping[selected_emoji]
        self.parent_view.personality_counter.update(traits)
        await self.parent_view.next_question(interaction)

class DivisionView(View):
    def __init__(self, bot, questions, divisions, channel):
        super().__init__(timeout=120)
        self.bot = bot
        self.questions = questions
        self.divisions = divisions
        self.channel = channel
        self.q_index = 0
        self.message = None
        self.personality_counter = Counter()
        self.add_question()

    def add_question(self):
        if self.q_index < len(self.questions):
            self.clear_items()
            self.add_item(QuestionSelect(self, self.questions[self.q_index], self.q_index))

    async def next_question(self, interaction: discord.Interaction):
        self.q_index += 1
        if self.q_index < len(self.questions):
            self.add_question()
            embed = discord.Embed(
                title=f"🧠 Test de division — Question {self.q_index + 1}/{len(self.questions)}",
                description=f"**{self.questions[self.q_index]['question']}**",
                color=discord.Color.orange()
            )
            await safe_edit(self.message, embed=embed, view=self)
        else:
            # Calculer la division finale
            division_scores = {
                div: sum(self.personality_counter[trait] for trait in info["traits"])
                for div, info in self.divisions.items()
            }
            best_division = max(division_scores, key=division_scores.get)
            embed_result = discord.Embed(
                title="🧩 Résultat de ton test",
                description=f"Tu serais dans la **{best_division}** !",
                color=discord.Color.green()
            )
            embed_result.set_image(url=f"attachment://{os.path.basename(self.divisions[best_division]['image'])}")
            await safe_edit(self.message, embed=embed_result, view=None)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Division(commands.Cog):
    """Commande /division et !division — Détermine ta division dans le Gotei 13."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _start_quiz(self, channel):
        data = load_division_data()
        if not data:
            await safe_send(channel, "❌ Impossible de charger les données.")
            return

        questions = random.sample(data["questions"], k=10)
        divisions = data["divisions"]
        view = DivisionView(self.bot, questions, divisions, channel)
        embed = discord.Embed(
            title=f"🧠 Test de division — Question 1/10",
            description=f"**{questions[0]['question']}**",
            color=discord.Color.orange()
        )
        view.message = await safe_send(channel, embed=embed, view=view)

    # ──────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ──────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="division",
        description="Détermine ta division dans le Gotei 13."
    )
    @app_commands.checks.cooldown(rate=1, per=5.0, key=lambda i: i.user.id)
    async def slash_division(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._start_quiz(interaction.channel)
        await interaction.delete_original_response()

    # ──────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ──────────────────────────────────────────────────────────────────────────────
    @commands.command(name="division")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_division(self, ctx: commands.Context):
        await self._start_quiz(ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Division(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
