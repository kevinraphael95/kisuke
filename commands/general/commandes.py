import discord
from discord.ext import commands
from bot import get_prefix  # pour récupérer le préfixe dynamique

class CommandesCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commandes", help="Affiche toutes les commandes disponibles du bot.")
    async def commandes(self, ctx):
        prefix = get_prefix(self.bot, ctx.message)

        description = ""
        for cmd in self.bot.commands:
            if not cmd.hidden:
                description += f"`{prefix}{cmd.name}` : {cmd.help or 'Aucune description.'}\n"

        embed = discord.Embed(
            title="📜 Liste complète des commandes",
            description=description or "Aucune commande trouvée.",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Utilise {prefix}help <commande> pour plus de détails sur une commande.")
        await ctx.send(embed=embed)

    @commandes.before_invoke
    async def set_category(self, ctx):
        self.commandes.category = "Général"

# Chargement automatique de l’extension
async def setup(bot):
    await bot.add_cog(CommandesCommand(bot))
