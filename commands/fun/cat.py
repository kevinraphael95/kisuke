import discord
from discord.ext import commands
import aiohttp
import io

class CatCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cat", help="Affiche une photo de chat mignon.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 Cooldown 3 secondes
    async def cat(self, ctx):
        # 🐾 Requête à l'API Cataas pour une image de chat
        async with aiohttp.ClientSession() as session:
            async with session.get("https://cataas.com/cat") as response:
                if response.status == 200:
                    image_data = await response.read()
                    image_file = discord.File(io.BytesIO(image_data), filename="cat.jpg")
                    await ctx.send("Voici un minou aléatoire ! 🐱", file=image_file)
                else:
                    await ctx.send("😿 Impossible de récupérer une image de chat.")

    def cog_load(self):
        self.cat.category = "Fun"  # ✅ Pour que !help classe bien la commande

# Chargement automatique
async def setup(bot):
    await bot.add_cog(CatCommand(bot))
