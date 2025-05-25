import discord
from discord.ext import commands
from discord.ext.commands import Context
from discord.ui import View, Select, select
from bot import get_prefix

class CommandesView(View):
    def __init__(self, bot, prefix):
        super().__init__(timeout=60)
        self.bot = bot
        self.prefix = prefix

        self.categories = {
            "Général": [],
            "Fun": [],
            "Reiatsu": [],
            "Admin": [],
            "Autres": []
        }

        for cmd in bot.commands:
            if cmd.hidden:
                continue
            cat = getattr(cmd, "category", "Autres")
            self.categories.setdefault(cat, []).append(cmd)

        for cmds in self.categories.values():
            cmds.sort(key=lambda c: c.name)

        options = [
            discord.SelectOption(label=cat, description=f"{len(cmds)} commande(s)", value=cat)
            for cat, cmds in self.categories.items() if cmds
        ]

        self.add_item(
            Select(
                placeholder="Choisis une catégorie de commandes...",
                options=options,
                min_values=1,
                max_values=1,
                custom_id="select_commandes"
            )
        )

    @select(custom_id="select_commandes")
    async def select_callback(self, interaction: discord.Interaction, select: Select):
        cat = select.values[0]
        cmds = self.categories[cat]

        embed = discord.Embed(
            title=f"📂 Commandes : {cat}",
            color=discord.Color.blurple()
        )
        for cmd in cmds:
            embed.add_field(
                name=f"`{self.prefix}{cmd.name}`",
                value=cmd.help or "Pas de description.",
                inline=False
            )

        embed.set_footer(text=f"Utilise {self.prefix}help <commande> pour plus d'infos.")
        await interaction.response.edit_message(embed=embed, view=self)

class CommandesCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commandes", help="Affiche les commandes classées par catégorie via un menu interactif.")
    async def commandes(self, ctx: Context):
        prefix = get_prefix(self.bot, ctx.message)
        view = CommandesView(self.bot, prefix)
        await ctx.send("📜 Choisis une catégorie pour voir les commandes disponibles :", view=view)

    @commandes.before_invoke
    async def set_category(self, ctx):
        self.commandes.category = "Général"

# Chargement du cog
async def setup(bot):
    await bot.add_cog(CommandesCommand(bot))
