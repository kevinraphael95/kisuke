# ────────────────────────────────────────────────────────────────────────────────
# 📌 tram_probleme.py — Commande /tram_probleme et !tram_probleme
# Objectif : Quiz interactif du dilemme du tramway avec compteur de folie
# Catégorie : Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond  # ✅ Utilitaires sécurisés
import json
import random
import os

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class TramProbleme(commands.Cog):
    """
    Commande /tram_probleme et !tram_probleme — Quiz du dilemme du tramway
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.questions_path = os.path.join("data", "tram_questions.json")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Chargement du JSON
    # ────────────────────────────────────────────────────────────────────────────
    def load_questions(self):
        try:
            with open(self.questions_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("questions", [])
        except Exception as e:
            print(f"[ERREUR] Impossible de charger le fichier JSON : {e}")
            return []

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="tram_probleme",
        description="Teste ta morale dans un quiz absurde du dilemme du tramway."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_tram_probleme(self, interaction: discord.Interaction):
        """Commande slash interactive"""
        await self.run_tram_quiz(interaction)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="tram_probleme",aliases=["tp"])
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_tram_probleme(self, ctx: commands.Context):
        """Commande préfixe interactive"""
        await self.run_tram_quiz(ctx)

    # ────────────────────────────────────────────────────────────────────────────
    # 🎮 Fonction principale du quiz
    # ────────────────────────────────────────────────────────────────────────────
    async def run_tram_quiz(self, ctx_or_inter):
        is_interaction = isinstance(ctx_or_inter, discord.Interaction)
        send = safe_respond if is_interaction else safe_send

        questions = self.load_questions()
        if not questions:
            await send(ctx_or_inter, "❌ Aucune question trouvée dans le JSON.")
            return

        random.shuffle(questions)
        score = 0
        folie = 0

        await send(ctx_or_inter, "🚋 **Bienvenue dans le Dilemme du Tramway : le Quiz Moralo-Absurde !**\nPrépare-toi à remettre ton éthique en question...")

        for i, question in enumerate(questions[:5], start=1):  # 5 questions max
            embed = discord.Embed(
                title=f"🚨 Question {i}/{min(5, len(questions))}",
                description=question["question"],
                color=discord.Color.orange()
            )
            embed.set_footer(text="Fais ton choix moral... ou pas 😈")

            view = discord.ui.View(timeout=60)

            # Création dynamique des boutons
            for option in question["options"]:
                button = discord.ui.Button(label=option, style=discord.ButtonStyle.primary)

                async def button_callback(interaction, choice=option):
                    nonlocal score, folie
                    result = question.get("results", {}).get(choice, "🤔 Choix étrange...")
                    score += question.get("scores", {}).get(choice, 0)
                    folie += question.get("folie", {}).get(choice, 0)

                    await interaction.response.send_message(
                        f"🧠 Tu as choisi : **{choice}**\n{result}",
                        ephemeral=True
                    )
                    view.stop()

                button.callback = button_callback
                view.add_item(button)

            await send(ctx_or_inter, embed=embed, view=view)

            # Attente de la fin du choix
            if isinstance(ctx_or_inter, discord.Interaction):
                await view.wait()
            else:
                await view.wait()

        # ────────────────────────────────────────────────────────────────────
        # 📊 Résultats finaux
        # ────────────────────────────────────────────────────────────────────
        embed_result = discord.Embed(
            title="🎉 Résultats du Dilemme du Tramway",
            color=discord.Color.green()
        )
        embed_result.add_field(name="🧾 Score moral", value=f"{score} points", inline=False)
        embed_result.add_field(name="🤪 Niveau de folie", value=f"{folie}/100", inline=False)

        # Petit message de fin absurde selon la folie
        if folie < 20:
            phrase = "Tu es moralement stable... pour l’instant 😇"
        elif folie < 60:
            phrase = "Tu sembles apprécier les dilemmes étranges 😈"
        else:
            phrase = "Le tramway n’est plus ton ami... tu es devenu le tramway. 🚋💀"

        embed_result.set_footer(text=phrase)
        await send(ctx_or_inter, embed=embed_result)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TramProbleme(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
