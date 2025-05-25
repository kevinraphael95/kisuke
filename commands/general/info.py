import discord
from discord.ext import commands

class InfoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="info", help="Affiche des informations sur l'état du bot.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 Cooldown 3s
    async def info(self, ctx):
        embed = discord.Embed(
            title="📊 État du bot",
            description="Voici quelques informations sur l'état actuel du bot.",
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🔧 Réorganisation",
            value="Le **code du bot** a été complètement **réorganisé**. Toutes les commandes ne sont plus dans un seul fichier `bot.py`.",
            inline=False
        )

        embed.add_field(
            name="📘 Commande help",
            value="La **commande help** sera réparée quand elle sera réparée.",
            inline=False
        )


        embed.add_field(
            name="💠 Reiatsu",
            value="Le spawn auto de reiatsu est de retour, normalement.",
            inline=False
        )


        embed.add_field(
            name="🧘 Nouvelles commandes",
            value="- tupref\n- topperso",
            inline=False
        )

        embed.set_footer(text="Dernière mise à jour : Mai 2025")
        await ctx.send(embed=embed)

    # ✅ Attribue la catégorie au bon moment
    @info.before_invoke
    async def before_info(self, ctx):
        self.info.category = "Général"

# 🔁 Chargement automatique
async def setup(bot):
    await bot.add_cog(InfoCommand(bot))
