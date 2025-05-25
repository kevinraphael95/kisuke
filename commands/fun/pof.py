import random
from discord.ext import commands

class PofCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pof", help="Lance une pièce : pile ou face.")
    async def pof(self, ctx):
        resultat = random.choice(["🪙 Pile !", "🪙 Face !"])
        await ctx.send(resultat)

# Chargement automatique
async def setup(bot):
    cog = PofCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
