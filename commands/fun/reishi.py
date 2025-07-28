# ────────────────────────────────────────────────────────────────────────────────
# 📌 reishi.py — Mini-jeu de réflexe !reishi
# Objectif : Cliquer quand le Reishi est stabilisé (curseur sur 🟩)
# Catégorie : Jeux
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import random
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# ⚡ Vue interactive — Canalisation du Reishi
# ────────────────────────────────────────────────────────────────────────────────
class ReishiView(View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=10)
        self.author = author
        self.position = 0
        self.zone = random.randint(3, 6)  # Position de la zone 🟩
        self.clicked = False
        self.message = None
        self.running = True

        self.add_item(ReishiButton(self))

    def build_bar(self):
        bar = []
        for i in range(9):
            if i == self.zone:
                bar.append("🟩")
            elif i in (self.zone - 1, self.zone + 1):
                bar.append("🟥")
            else:
                bar.append("⬛")

        if self.position < len(bar):
            bar[self.position] = "🔘"
        return "".join(bar)

    def build_embed(self):
        embed = discord.Embed(
            title="🔮 Reishi Instable",
            description="Clique quand l'énergie est **stabilisée** !",
            color=discord.Color.purple()
        )
        embed.add_field(name="Canalisation du Reishi", value=self.build_bar(), inline=False)
        embed.set_footer(text="Timing parfait requis.")
        return embed

    async def start_loop(self):
        while self.position < 9 and not self.clicked:
            await asyncio.sleep(0.5)
            self.position += 1
            if self.message:
                await safe_edit(self.message, embed=self.build_embed(), view=self)
        if not self.clicked:
            await self.fail()

    async def handle_click(self, interaction: discord.Interaction):
        self.clicked = True
        self.stop()
        if self.position == self.zone:
            await self.success(interaction)
        else:
            await self.fail(interaction)

    async def success(self, interaction):
        embed = discord.Embed(
            title="✅ Reishi Stabilisé !",
            description="Tu as canalisé l'énergie avec précision.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)

    async def fail(self, interaction=None):
        self.stop()
        embed = discord.Embed(
            title="❌ Échec de canalisation",
            description="L'énergie t'a échappé… essaie encore.",
            color=discord.Color.red()
        )
        if interaction:
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            await safe_edit(self.message, embed=embed, view=None)

# ────────────────────────────────────────────────────────────────────────────────
# 🎯 Bouton de tentative
# ────────────────────────────────────────────────────────────────────────────────
class ReishiButton(Button):
    def __init__(self, view: ReishiView):
        super().__init__(label="Canaliser !", style=discord.ButtonStyle.primary)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await interaction.response.send_message("⛔ Ce Reishi ne t'appartient pas.", ephemeral=True)
        if not self.view_ref.clicked:
            await self.view_ref.handle_click(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Reishi(commands.Cog):
    """
    Commande !reishi — Mini-jeu de réflexe pour canaliser le Reishi
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="reishi",
        help="Mini-jeu de réflexe : clique au bon moment pour stabiliser le Reishi.",
        description="Un seul clic pour réussir ou échouer la canalisation."
    )
    async def reishi(self, ctx: commands.Context):
        view = ReishiView(ctx.author)
        embed = view.build_embed()
        msg = await safe_send(ctx, embed=embed, view=view)
        view.message = msg
        await view.start_loop()

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Reishi(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
