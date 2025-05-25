import discord
import json
import random
from discord.ext import commands

class PhraseCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="phrase", help="Génère une phrase aléatoire avec accords (via JSON).")
    async def phrase(self, ctx):
        try:
            with open("data/phrases_listes.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            sujet_data = random.choice(data["sujets"])
            sujet = sujet_data["mot"]
            genre_sujet = sujet_data["genre"]

            verbe = random.choice(data["verbes"])

            complement_data = random.choice(data["complements"])
            complement = complement_data["mot"]
            genre_complement = complement_data["genre"]

            adverbe = random.choice(data["adverbes"])

            # Détermination de l’article pour le sujet
            if sujet[0].lower() in "aeiou":
                article_sujet = "L'"
            else:
                article_sujet = "Le " if genre_sujet == "m" else "La "

            # Détermination de l’article pour le complément
            if complement[0].lower() in "aeiou":
                article_complement = "l'"
            else:
                article_complement = "le " if genre_complement == "m" else "la "

            phrase_complete = f"{article_sujet}{sujet} {verbe} {article_complement}{complement} {adverbe}."
            await ctx.send(phrase_complete)

        except FileNotFoundError:
            await ctx.send("❌ Fichier `phrases_listes.json` introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : {e}")

# Chargement automatique
async def setup(bot):
    cog = PhraseCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
