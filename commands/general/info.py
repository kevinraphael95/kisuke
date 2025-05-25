import discord
from discord.ext import commands

class InfoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="info", help="Affiche des informations sur l'état du bot.")
    async def info(self, ctx):
        embed = discord.Embed(
            title="📊 État du bot",
            description="Voici quelques informations sur l'état actuel du bot.",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🔧 Réorganisation",
            value="Le **code du bot** a été complètement **réorganisé**.",
            inline=False
        )

        embed.add_field(
            name="🧘 Commandes Reiatsu",
            value="Les **commandes Reiatsu** ont été **supprimées** temporairement.\n"
                  "Elles seront **réintégrées si possible** prochainement.",
            inline=False
        )

        embed.set_footer(text="Dernière mise à jour : Mai 2025")
        await ctx.send(embed=embed)

    @info.before_invoke
    async def before_info(self, ctx):
        self.info.category = "Général"

# Chargement automatique
async def setup(bot):
    await bot.add_cog(InfoCommand(bot))
