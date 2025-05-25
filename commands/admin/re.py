import discord
from discord.ext import commands

class RedemarrageCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="re", help="(Admin) Préviens les membres du redémarrage du bot.")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def re(self, ctx):
        # Essaye de supprimer le message de commande
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass  # Ignore si le bot n'a pas la permission

        # Envoie l'embed de redémarrage
        embed = discord.Embed(
            title="🔃 Redémarrage",
            description="Le bot va redémarrer sous peu.",
            color=discord.Color.red()
        )

# Chargement automatique
async def setup(bot):
    cog = RedemarrageCommand(bot)
    for command in cog.get_commands():
        command.category = "Admin"
    await bot.add_cog(cog)
