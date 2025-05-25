import discord
from discord.ext import commands

class PingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", aliases=["test"], help="Répond avec la latence du bot.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown de 3s par utilisateur
    async def ping(self, ctx):
        latence = round(self.bot.latency * 1000)  # Convertit en ms
        embed = discord.Embed(
            title="🏓 Pong !",
            description=f"📶 Latence : `{latence} ms`",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    def cog_load(self):
        self.ping.category = "Général"  # ✅ Définit la catégorie visible dans !help

# Chargement automatique du module
async def setup(bot):
    await bot.add_cog(PingCommand(bot))
