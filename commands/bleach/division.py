# ────────────────────────────────────────────────────────────────────────────────
# 📌 division.py — Commande interactive /division et !division
# Objectif : Déterminer ta division via un QCM avec choix limité (4 réponses aléatoires)
# Catégorie : Bleach
# Accès : Tous
# Cooldown : 1 essai / 5s
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

from utils.discord_utils import safe_send, safe_edit, safe_respond, safe_delete

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "divisions_quiz.json")

def load_data():
    """Charge le fichier JSON contenant les divisions et questions."""
    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {DATA_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu de sélection pour une question
# ────────────────────────────────────────────────────────────────────────────────
class QuestionSelect(Select):
    def __init__(self, parent_view, question, answers):
        options = [
            discord.SelectOption(label=ans, description=None)
            for ans in answers.keys()
        ]
        super().__init__(placeholder=question, options=options, min_values=1, max_values=1)
        self.parent_view = parent_view
        self.answers = answers

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        self.parent_view.counter.update(self.answers[selected])
        await interaction.response.defer()
        self.parent_view.stop()

class QuestionView(View):
    def __init__(self, bot, question, answers, counter):
        super().__init__(timeout=60)
        self.bot = bot
        self.counter = counter
        self.add_item(QuestionSelect(self, question, answers))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Division(commands.Cog):
    """Commande / !division — Détermine ta division du Gotei 13"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def run_quiz(self, ctx_or_interaction):
        data = load_data()
        if not data:
            await safe_respond(ctx_or_interaction, "❌ Données introuvables.")
            return

        questions = random.sample(data["questions"], k=10)  # 10 questions aléatoires
        divisions = data["divisions"]
        personality_counter = Counter()

        for idx, q in enumerate(questions, start=1):
            # Choisir 4 réponses au hasard
            all_answers = list(q["answers"].items())
            selected_answers = dict(random.sample(all_answers, 4))

            view = QuestionView(self.bot, f"Q{idx}/10 — {q['question']}", selected_answers, personality_counter)
            embed = discord.Embed(
                title=f"🧠 Test Division — Question {idx}/10",
                description="Choisis ta réponse dans le menu déroulant.",
                color=discord.Color.orange()
            )

            if isinstance(ctx_or_interaction, discord.Interaction):
                message = await safe_respond(ctx_or_interaction, embed=embed, view=view)
            else:
                message = await safe_send(ctx_or_interaction.channel, embed=embed, view=view)

            await view.wait()

            try:
                await safe_edit(message, embed=embed, view=None)
            except:
                pass

        # Résultat final
        division_scores = {
            div: sum(personality_counter[trait] for trait in info["traits"])
            for div, info in divisions.items()
        }
        best_division = max(division_scores, key=division_scores.get)

        embed_result = discord.Embed(
            title="🧩 Résultat du test",
            description=f"Tu appartiendrais à la **{best_division}** !",
            color=discord.Color.green()
        )
        embed_result.set_image(url=f"attachment://{os.path.basename(divisions[best_division]['image'])}")

        if isinstance(ctx_or_interaction, discord.Interaction):
            await safe_respond(ctx_or_interaction, embed=embed_result)
        else:
            await safe_send(ctx_or_interaction.channel, embed=embed_result)

    # Commande préfixée
    @commands.command(name="division", help="Détermine ta division du Gotei 13")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def division_prefix(self, ctx: commands.Context):
        await self.run_quiz(ctx)

    # Commande slash
    @app_commands.command(name="division", description="Détermine ta division du Gotei 13")
    async def division_slash(self, interaction: discord.Interaction):
        await self.run_quiz(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Division(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
        
