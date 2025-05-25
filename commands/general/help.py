import discord
from discord.ext import commands
from bot import get_prefix  # uniquement la fonction

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", help="Affiche la liste des commandes ou les infos sur une commande spécifique.")
    async def help_command(self, ctx, commande: str = None):
        prefix = get_prefix(self.bot, ctx.message)

        if commande is None:
            categories = {
                "Général": [],
                "Fun": [],
                "Reiatsu": [],
                "Admin": [],
                "Autres": []
            }

            for cmd in self.bot.commands:
                if cmd.hidden:
                    continue
                cat = getattr(cmd, "category", "Autres")
                categories.setdefault(cat, []).append(cmd)

            embed = discord.Embed(title="📜 Commandes par catégorie", color=discord.Color.blue())

            for cat in ["Général", "Fun", "Reiatsu", "Admin", "Autres"]:
                cmds = categories.get(cat, [])
                if cmds:
                    cmds.sort(key=lambda c: c.name)
                    liste = "\n".join(f"`{prefix}{cmd.name}` : {cmd.help or 'Pas de description.'}" for cmd in cmds)
                    embed.add_field(name=f"📂 {cat}", value=liste, inline=False)

            embed.set_footer(text=f"Utilise {prefix}help <commande> pour plus de détails.")
            await ctx.send(embed=embed)

        else:
            cmd = self.bot.get_command(commande)
            if cmd is None:
                await ctx.send(f"❌ La commande `{commande}` n'existe pas.")
            else:
                embed = discord.Embed(
                    title=f"Aide pour `{prefix}{cmd.name}`",
                    color=discord.Color.green()
                )
                embed.add_field(name="Description", value=cmd.help or "Pas de description.", inline=False)
                if cmd.aliases:
                    embed.add_field(name="Alias", value=", ".join(f"`{a}`" for a in cmd.aliases), inline=False)
                embed.set_footer(text="Paramètres entre < > = obligatoires | [ ] = optionnels")
                await ctx.send(embed=embed)

    # Ajoute la catégorie directement après définition
    help_command.category = "Général"

# Chargement auto
async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
    print("✅ Commande help chargée")
