import discord
from discord.ext import commands
from discord.ext.commands import Context
from bot import get_prefix

class CommandesCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commandes", help="Affiche toutes les commandes disponibles, classées par catégorie.")
    async def commandes(self, ctx: Context):
        prefix = get_prefix(self.bot, ctx.message)

        # Regrouper les commandes par catégorie
        categories = {}
        for cmd in self.bot.commands:
            if cmd.hidden:
                continue
            cat = getattr(cmd, "category", "Autres")
            categories.setdefault(cat, []).append(cmd)

        # Générer un embed par catégorie
        embeds = []
        for cat, cmds in sorted(categories.items()):
            cmds.sort(key=lambda c: c.name)
            description = "\n".join(f"`{prefix}{cmd.name}` : {cmd.help or 'Pas de description.'}" for cmd in cmds)

            embed = discord.Embed(
                title=f"📂 Catégorie : {cat}",
                description=description,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Utilise !help <commande> pour plus de détails.")
            embeds.append(embed)

        # Afficher le premier embed
        message = await ctx.send(embed=embeds[0])
        if len(embeds) <= 1:
            return

        # Ajouter les réactions de navigation
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")

        current_page = 0

        def check(reaction, user):
            return (
                user == ctx.author
                and str(reaction.emoji) in ["⬅️", "➡️"]
                and reaction.message.id == message.id
            )

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                if str(reaction.emoji) == "➡️":
                    current_page = (current_page + 1) % len(embeds)
                elif str(reaction.emoji) == "⬅️":
                    current_page = (current_page - 1) % len(embeds)

                await message.edit(embed=embeds[current_page])
                await message.remove_reaction(reaction, user)

            except Exception:
                break  # Timeout ou erreur : arrêter la pagination

    @commandes.before_invoke
    async def set_category(self, ctx):
        self.commandes.category = "Général"

# Chargement de l'extension
async def setup(bot):
    await bot.add_cog(CommandesCommand(bot))
