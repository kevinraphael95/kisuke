import discord
import json
import random
from discord.ext import commands

class FunFactCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="funfact", help="Donne un funfact sur Bleach écrit par ChatGPT.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown 3s
    async def funfact(self, ctx):
        try:
            with open("data/funfacts_bleach.json", "r", encoding="utf-8") as f:
                facts = json.load(f)

            if not facts:
                await ctx.send("❌ Aucun fun fact disponible.")
                return

            fact = random.choice(facts)
            await ctx.send(f"🧠 **Fun Fact Bleach :** {fact}")

        except FileNotFoundError:
            await ctx.send("❌ Fichier `funfacts_bleach.json` introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : {e}")

    def cog_load(self):
        self.funfact.category = "Fun"  # ✅ Catégorie assignée proprement

# Chargement automatique du cog
async def setup(bot):
    await bot.add_cog(FunFactCommand(bot))
