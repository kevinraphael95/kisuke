import aiohttp
import discord
from discord.ext import commands

class DogCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="dog", help="Montre une photo aléatoire d'un chien")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown 3s
    async def dog(self, ctx):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog.ceo/api/breeds/image/random") as response:
                if response.status == 200:
                    data = await response.json()
                    image_url = data["message"]
                    await ctx.send(f"Voici un toutou aléatoire ! 🐶\n{image_url}")
                else:
                    await ctx.send("❌ Impossible de récupérer une image de chien 😢")

    def cog_load(self):
        self.dog.category = "Fun"  # ✅ Assignation de la catégorie

# Chargement automatique
async def setup(bot):
    await bot.add_cog(DogCommand(bot))
