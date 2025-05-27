import discord
from discord.ext import commands
from bot import get_prefix

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", help="Affiche la liste des commandes ou les infos sur une commande spécifique.")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def help_func(self, ctx, commande: str = None):
        prefix = get_prefix(self.bot, ctx.message)

        if commande is None:
            categories = {}

            for cmd in self.bot.commands:
                if cmd.hidden:
                    continue
                cat = getattr(cmd, "category", "Autres")
                categories.setdefault(cat, []).append(cmd)

            embed = discord.Embed(title="📜 Commandes par catégorie", color=discord.Color.blue())

            for cat, cmds in categories.items():
                cmds.sort(key=lambda c: c.name)
                description = "\n".join(f"`{prefix}{c.name}` : {c.help or 'Pas de description.'}" for c in cmds)
                embed.add_field(name=f"📂 {cat}", value=description, inline=False)

            embed.set_footer(text=f"Utilise {prefix}help <commande> pour plus de détails.")
            await ctx.send(embed=embed)

        else:
            cmd = self.bot.get_command(commande)
            if cmd is None:
                await ctx.send(f"❌ La commande `{commande}` n'existe pas.")
                return

            embed = discord.Embed(
                title=f"Aide pour `{prefix}{cmd.name}`",
                color=discord.Color.green()
            )
            embed.add_field(name="Description", value=cmd.help or "Pas de description.", inline=False)
            if cmd.aliases:
                embed.add_field(name="Alias", value=", ".join(f"`{a}`" for a in cmd.aliases), inline=False)
            embed.set_footer(text="Paramètres entre < > = obligatoires | [ ] = optionnels")
            await ctx.send(embed=embed)

# Chargement
async def setup(bot):
    cog = HelpCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
