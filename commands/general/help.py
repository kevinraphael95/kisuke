import discord
from discord.ext import commands
from bot import get_prefix  # ta fonction perso pour le préfixe

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", help="Affiche la liste des commandes ou les infos sur une commande spécifique.")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def afficher_aide(self, ctx, commande: str = None):  # ✅ nom différent ici
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

            embed = discord.Embed(
                title="📜 Commandes disponibles",
                description=f"Utilise `{prefix}help <commande>` pour plus d'infos.",
                color=discord.Color.blue()
            )

            for cat, cmds in categories.items():
                if cmds:
                    cmds.sort(key=lambda c: c.name)
                    liste = "\n".join(f"`{prefix}{cmd.name}` : {cmd.help or 'Pas de description.'}" for cmd in cmds)
                    embed.add_field(name=f"📂 {cat}", value=liste, inline=False)

            await ctx.send(embed=embed)
        else:
            cmd = self.bot.get_command(commande)
            if cmd is None:
                await ctx.send(f"❌ La commande `{commande}` n'existe pas.")
                return

            embed = discord.Embed(
                title=f"ℹ️ Aide pour `{prefix}{cmd.name}`",
                color=discord.Color.green()
            )
            embed.add_field(name="Description", value=cmd.help or "Pas de description.", inline=False)
            if cmd.aliases:
                embed.add_field(name="Alias", value=", ".join(f"`{a}`" for a in cmd.aliases), inline=False)
            embed.set_footer(text="Paramètres entre < > = obligatoires | [ ] = optionnels")
            await ctx.send(embed=embed)

# ✅ Setup du cog avec catégorie
async def setup(bot):
    cog = HelpCommand(bot)
    for command in cog.get_commands():
        command.category = "Général"
    await bot.add_cog(cog)
