# ────────────────────────────────────────────────────────────────────────────────
# 📌 demineur.py — Commande interactive /demineur et !demineur
# Objectif : Lancer une partie de démineur solo ou multi-joueurs
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random
import asyncio

from utils.discord_utils import safe_send, safe_edit, safe_respond, safe_delete

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Boutons du plateau
# ────────────────────────────────────────────────────────────────────────────────
class MineButton(Button):
    def __init__(self, x, y, parent_view):
        super().__init__(label="⬜", style=discord.ButtonStyle.secondary, row=y)
        self.x = x
        self.y = y
        self.parent_view = parent_view
        self.revealed = False

    async def callback(self, interaction: discord.Interaction):
        if self.revealed:
            return
        self.revealed = True
        cell_value = self.parent_view.board[self.y][self.x]
        if cell_value == "💣":
            self.style = discord.ButtonStyle.danger
            self.label = "💣"
            await interaction.response.edit_message(view=self.parent_view)
            await safe_send(interaction.channel, f"💥 Boom ! Partie terminée.")
            self.parent_view.stop()
        else:
            self.style = discord.ButtonStyle.success
            self.label = str(cell_value) if cell_value > 0 else "▫️"
            await interaction.response.edit_message(view=self.parent_view)
            self.parent_view.check_victory()

class DemineurView(View):
    def __init__(self, bot, size=5, mines=5):
        super().__init__(timeout=300)
        self.bot = bot
        self.size = size
        self.mines = mines
        self.message = None
        self.board = self.generate_board()
        for y in range(size):
            for x in range(size):
                self.add_item(MineButton(x, y, self))

    def generate_board(self):
        # Génère une grille avec des mines et nombres
        board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        mine_coords = random.sample([(x, y) for x in range(self.size) for y in range(self.size)], self.mines)
        for x, y in mine_coords:
            board[y][x] = "💣"
        # Compte les mines autour
        for y in range(self.size):
            for x in range(self.size):
                if board[y][x] == "💣":
                    continue
                count = 0
                for dy in (-1,0,1):
                    for dx in (-1,0,1):
                        ny, nx = y+dy, x+dx
                        if 0 <= nx < self.size and 0 <= ny < self.size and board[ny][nx] == "💣":
                            count += 1
                board[y][x] = count
        return board

    def check_victory(self):
        if all(
            isinstance(button.label, str) and (button.label != "⬜" or button.label == "💣")
            for button in self.children
        ):
            if self.message:
                asyncio.create_task(safe_send(self.message.channel, "🏆 Félicitations ! Vous avez gagné !"))
            self.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Demineur(commands.Cog):
    """Commande /demineur et !demineur — Lance une partie de démineur"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_game(self, channel: discord.abc.Messageable):
        """Envoie le plateau de démineur interactif"""
        view = DemineurView(self.bot)
        view.message = await safe_send(channel, "💣 Démineur — Clique sur les cases pour découvrir !", view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="demineur",
        description="Lance une partie de démineur."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_demineur(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._send_game(interaction.channel)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /demineur] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="demineur")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_demineur(self, ctx: commands.Context):
        try:
            await self._send_game(ctx.channel)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !demineur] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Demineur(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
