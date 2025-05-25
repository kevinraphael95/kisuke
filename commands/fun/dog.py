import aiohttp
import discord
from discord.ext import commands

class DogCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dog", help="Montre une photo aléatoire d'un chien")
    async def dog(self, ctx):
        # 📡 Requête vers l'API dog.ceo
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as response:
                if response.status == 200:
                    data = await response.json()
                    image_url = data["message"]
                    await ctx.send(f"Voici un toutou aléatoire ! 🐶\n{image_url}")
                else:
                    await ctx.send("❌ Impossible de récupérer une image de chien 😢")

# Chargement automatique + ajout de catégorie
async def setup(bot):
    cog = DogCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
