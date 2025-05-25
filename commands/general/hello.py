import os
import json
import random
import discord
from discord.ext import commands

class HelloCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hello", help="Affiche un message de bienvenue aléatoire.")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)  # ⏱️ Cooldown utilisateur 10s
    async def hello(self, ctx):
        try:
            # Lecture depuis le dossier data/
            with open("data/hello_messages.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                messages = data.get("messages", [])
            
            # Choix aléatoire d’un message ou fallback
            if messages:
                await ctx.send(random.choice(messages))
            else:
                await ctx.send("👋 Hello, je suis en ligne (mais sans message personnalisé) !")

        except FileNotFoundError:
            await ctx.send("❌ Fichier `hello_messages.json` introuvable dans le dossier `data/`.")
        except json.JSONDecodeError:
            await ctx.send("❌ Erreur de lecture du fichier `hello_messages.json`.")

# Chargement automatique
async def setup(bot):
    await bot.add_cog(HelloCommand(bot))
