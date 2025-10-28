# ────────────────────────────────────────────────────────────────────────────────
# 📌 tram_probleme.py — Commande /tram_probleme et !tram_probleme
# Objectif : Quiz interactif du dilemme du tramway avec compteur de folie + mode story
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
    @app_commands.describe(story="Active le mode histoire complète (toutes les questions enchaînées dans l'ordre).")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_tram_probleme(self, interaction: discord.Interaction, story: bool = False):
        """Commande slash interactive"""
        await self.run_tram_quiz(interaction, story)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="tram_probleme", aliases=["tp"])
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_tram_probleme(self, ctx: commands.Context, *args):
        """Commande préfixe interactive"""
        story = any(arg.lower() in ["story", "histoire", "mode_story"] for arg in args)
        await self.run_tram_quiz(ctx, story)

    # ────────────────────────────────────────────────────────────────────────────
    # 🎮 Fonction principale du quiz (améliorée)
    # ────────────────────────────────────────────────────────────────────────────
    async def run_tram_quiz(self, ctx_or_inter, story: bool = False):
        is_interaction = isinstance(ctx_or_inter, discord.Interaction)
        send = safe_respond if is_interaction else safe_send

        questions = self.load_questions()
        if not questions:
            await send(ctx_or_inter, "❌ Aucune question trouvée dans le JSON.")
            return

        if not story:
            random.shuffle(questions)

        score = 0
        folie = 0
        utilitarisme_count = 0
        deontologie_count = 0

        await send(
            ctx_or_inter,
            "🚋 **Bienvenue dans le Dilemme du Tramway !**\n"
            "Prépare-toi à remettre ton éthique en question...\n"
            f"🧩 Mode story : {'✅ Activé (ordre fixe)' if story else '❌ Désactivé (ordre aléatoire)'}"
        )

        total_q = len(questions) if story else min(5, len(questions))

        for i, question in enumerate(questions[:total_q], start=1):
            embed = discord.Embed(
                title=f"🚨 Question {i}/{total_q}",
                description=question["question"],
                color=discord.Color.orange()
            )
            embed.set_footer(text="Fais ton choix moral... ou pas 😈")

            view = discord.ui.View(timeout=60)
            answered = False

            for option in question["options"]:
                button = discord.ui.Button(label=option["text"], style=discord.ButtonStyle.primary)

                async def button_callback(interaction, choice=option):
                    nonlocal score, folie, utilitarisme_count, deontologie_count, answered
                    answered = True
                    result = choice.get("result", "🤔 Choix étrange...")
                    score += choice.get("score", 0)
                    folie += choice.get("folie", 0)

                    ethics_type = choice.get("ethics")
                    if ethics_type == "utilitarisme":
                        utilitarisme_count += 1
                    elif ethics_type == "déontologie":
                        deontologie_count += 1

                    await interaction.response.send_message(
                        f"🧠 Tu as choisi : **{choice['text']}**\n{result}",
                        ephemeral=True
                    )
                    view.stop()

                button.callback = button_callback
                view.add_item(button)

            await send(ctx_or_inter, embed=embed, view=view)
            timeout = await view.wait()

            if story and not answered:
                await send(ctx_or_inter, "⛔ Le tram s’arrête. Tu n’as pas répondu à temps.")
                return

            if story and i < total_q:
                await send(ctx_or_inter, "🚋 Le tramway continue sa route...\n")

        # ───────────────────────────────────────────────
        # Résultats finaux avec profil moral
        # ───────────────────────────────────────────────
        embed_result = discord.Embed(
            title="🎉 Résultats du Dilemme du Tramway",
            color=discord.Color.green()
        )
        embed_result.add_field(name="🧾 Score moral", value=f"{score} points", inline=False)
        embed_result.add_field(name="🤪 Niveau de folie", value=f"{folie}/100", inline=False)
        embed_result.add_field(
            name="⚖️ Équilibre éthique",
            value=f"Utilitarisme : {utilitarisme_count}\nDéontologie : {deontologie_count}",
            inline=False
        )

        if utilitarisme_count > deontologie_count:
            profil = "Tu es plutôt **utilitariste** – tu cherches à maximiser le bien global, quitte à salir tes mains. 🤔"
        elif deontologie_count > utilitarisme_count:
            profil = "Tu es plutôt **déontologique** – tu respectes les principes moraux, même face au chaos. 🧘"
        else:
            profil = "Ton équilibre moral est parfait : un tram entre la raison et la règle. 🚋⚖️"

        embed_result.add_field(name="🧭 Profil moral", value=profil, inline=False)

        if folie < 20:
            phrase = "Tu es moralement stable... pour l’instant 😇"
        elif folie < 60:
            phrase = "Tu sembles apprécier les dilemmes étranges 😈"
        else:
            phrase = "Le tramway n’est plus ton ami... tu **es** devenu le tramway. 🚋💀"

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
