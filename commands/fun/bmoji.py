import discord
from discord.ext import commands
import json
import random

class BMojiCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="bmoji", help="Devine quel personnage Bleach se cache derrière cet emoji.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown 3s
    async def bmoji(self, ctx):
        try:
            with open("data/bleach_emojis.json", "r", encoding="utf-8") as f:
                personnages = json.load(f)

            if not personnages:
                await ctx.send("⚠️ Le fichier d'emojis est vide.")
                return

            personnage = random.choice(personnages)
            nom = personnage.get("nom")
            emojis = personnage.get("emojis")

            if not nom or not emojis:
                await ctx.send("❌ Erreur de format dans le fichier JSON.")
                return

            emoji_selection = random.choice(emojis)
            await ctx.send(f"{emoji_selection} → ||{nom}||")

        except FileNotFoundError:
            await ctx.send("❌ Fichier `bleach_emojis.json` introuvable dans `data/`.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur inattendue : {e}")

    def cog_load(self):
        self.bmoji.category = "Fun"

async def setup(bot):
    await bot.add_cog(BMojiCommand(bot))
