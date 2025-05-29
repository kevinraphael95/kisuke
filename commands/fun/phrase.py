# ────────────────────────────────────────────────────────────────
#       🗣️ COMMANDE DISCORD - PHRASE ALÉATOIRE ACCORDÉE       
# ────────────────────────────────────────────────────────────────

import discord
import json
import random
from discord.ext import commands

# ────────────────────────────────────────────────────────────────═
# 📦 Classe principale de la commande "phrase"
# ────────────────────────────────────────────────────────────────═
class PhraseCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ───────────────────────────────────────────────
    # 🗣️ Commande !phrase : phrase accordée aléatoirement
    # ⏱️ Cooldown de 3 secondes par utilisateur
    # ───────────────────────────────────────────────
    @commands.command(
        name="phrase",
        help="📚 Génère une phrase aléatoire avec les bons accords (via JSON)."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def phrase(self, ctx):
        try:
            # 📂 Lecture du fichier JSON
            with open("data/phrases_listes.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            # 🎲 Sélections aléatoires
            sujet_data = random.choice(data["sujets"])
            sujet = sujet_data["mot"]
            genre_sujet = sujet_data["genre"]

            verbe = random.choice(data["verbes"])

            complement_data = random.choice(data["complements"])
            complement = complement_data["mot"]
            genre_complement = complement_data["genre"]

            adverbe = random.choice(data["adverbes"])

            # 🧠 Accord des articles définis
            article_sujet = "L'" if sujet[0].lower() in "aeiouéèê" else ("Le " if genre_sujet == "m" else "La ")
            article_complement = "l'" if complement[0].lower() in "aeiouéèê" else ("le " if genre_complement == "m" else "la ")

            # ✏️ Construction finale
            phrase_complete = f"{article_sujet}{sujet} {verbe} {article_complement}{complement} {adverbe}."
            await ctx.send(phrase_complete)

        except FileNotFoundError:
            await ctx.send("❌ Fichier `phrases_listes.json` introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : {e}")

    # ✅ Catégorie visible dans le !help
    def cog_load(self):
        self.phrase.category = "Fun"

# ────────────────────────────────────────────────────────────────═
# 🔌 Setup du module pour chargement automatique
# ────────────────────────────────────────────────────────────────═
async def setup(bot):
    cog = PhraseCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
