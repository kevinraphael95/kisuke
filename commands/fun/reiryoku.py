# ────────────────────────────────────────────────────────────────────────────────
# ⚡ reiryoku.py — Commande interactive !reiryoku
# Objectif : Mini-jeu zen d’harmonisation de Reiryoku (énergie spirituelle)
# Catégorie : Jeux
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands, tasks
from discord.ui import View, Button
import random
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Vue interactive Reiryoku
# ────────────────────────────────────────────────────────────────────────────────
class ReiryokuView(View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=30)
        self.author = author
        self.level_1 = 0
        self.level_2 = 4
        self.direction_1 = 1
        self.direction_2 = -1
        self.message = None
        self.running = True
        self.result_shown = False
        self.loop.start()
        self.add_item(CanaliserButton(self))

    def build_bar(self, level):
        bar = ["▫️"] * 5
        bar[level] = "🔷"
        return "".join(bar)

    def build_embed(self):
        embed = discord.Embed(
            title="🌀 Reiryoku — Harmonise ton énergie !",
            description=(
                "Clique sur **Canaliser** quand les deux flux sont alignés !\n"
                f"**Flux 1** : {self.build_bar(self.level_1)}\n"
                f"**Flux 2** : {self.build_bar(self.level_2)}"
            ),
            color=discord.Color.purple()
        )
        return embed

    @tasks.loop(seconds=0.5)
    async def loop(self):
        if not self.running or self.result_shown:
            return

        self.level_1 += self.direction_1
        self.level_2 += self.direction_2

        if self.level_1 in [0, 4]:
            self.direction_1 *= -1
        if self.level_2 in [0, 4]:
            self.direction_2 *= -1

        if self.message:
            await safe_edit(self.message, embed=self.build_embed(), view=self)

    async def stop_loop(self):
        self.running = False
        self.loop.stop()

    async def show_result(self, interaction: discord.Interaction):
        await self.stop_loop()
        self.result_shown = True

        diff = abs(self.level_1 - self.level_2)
        if diff == 0:
            result = "✅ Parfaitement synchronisé !"
            color = discord.Color.green()
        elif diff == 1:
            result = "🟢 Bien, mais tu peux faire mieux."
            color = discord.Color.orange()
        else:
            result = "🔴 Désynchronisation énergétique..."
            color = discord.Color.red()

        embed = discord.Embed(
            title="✨ Résultat de la canalisation",
            description=(
                f"**Flux 1** : {self.build_bar(self.level_1)}\n"
                f"**Flux 2** : {self.build_bar(self.level_2)}\n\n"
                f"{result}"
            ),
            color=color
        )
        await safe_respond(interaction, embed=embed, view=None)

# ────────────────────────────────────────────────────────────────────────────────
# ✋ Bouton "Canaliser"
# ────────────────────────────────────────────────────────────────────────────────
class CanaliserButton(Button):
    def __init__(self, view: ReiryokuView):
        super().__init__(label="Canaliser", style=discord.ButtonStyle.success)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await safe_respond(interaction, content="⛔ Ce jeu ne t'appartient pas.", ephemeral=True)

        await self.view_ref.show_result(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Reiryoku(commands.Cog):
    """
    Commande !reiryoku — Harmonise ton énergie spirituelle au bon moment
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="reiryoku",
        help="Mini-jeu d'équilibrage d'énergie spirituelle.",
        description="Clique quand les deux flux sont alignés."
    )
    async def reiryoku(self, ctx: commands.Context):
        view = ReiryokuView(ctx.author)
        embed = view.build_embed()
        msg = await safe_send(ctx, embed=embed, view=view)
        view.message = msg


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiryokuView(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
