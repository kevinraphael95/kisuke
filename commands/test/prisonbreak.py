# ────────────────────────────────────────────────────────────────────────────────
# 📌 prison_escape.py — Mini-jeu d'évasion : sortir d'une grille sans se faire attraper
# Objectif : Mini-jeu interactif avec grille, déplacements, et gardien
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View
import asyncio
from utils.discord_utils import safe_send, safe_edit, safe_add_reaction

# ────────────────────────────────────────────────────────────────────────────────
# 🧱 Constantes du jeu
# ────────────────────────────────────────────────────────────────────────────────
GRID_SIZE = 6
EMPTY = "⬜"
WALL = "⬛"
PLAYER = "😃"
GUARD = "👮"
EXIT = "🚪"

# Positions fixes (exemple)
START_POS = (0, 0)
EXIT_POS = (GRID_SIZE-1, GRID_SIZE-1)
WALLS = {(1, 2), (2, 2), (3, 2), (4, 4)}  # Exemple de murs

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Classe View du jeu
# ────────────────────────────────────────────────────────────────────────────────
class EscapePrisonView(View):
    def __init__(self, ctx, bot):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.bot = bot
        self.grid = [[EMPTY for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        for (x,y) in WALLS:
            self.grid[y][x] = WALL
        self.player_pos = START_POS
        self.guard_pos = (GRID_SIZE//2, GRID_SIZE//2)
        self.grid[self.player_pos[1]][self.player_pos[0]] = PLAYER
        self.grid[self.guard_pos[1]][self.guard_pos[0]] = GUARD
        self.grid[EXIT_POS[1]][EXIT_POS[0]] = EXIT
        self.message = None
        self.game_over = False

        # Ajout des boutons déplacement
        self.add_item(MoveButton("⬆️", (0, -1)))
        self.add_item(MoveButton("⬇️", (0, 1)))
        self.add_item(MoveButton("⬅️", (-1, 0)))
        self.add_item(MoveButton("➡️", (1, 0)))

    def render_grid(self):
        """Retourne la grille sous forme de texte avec emojis"""
        lines = []
        for row in self.grid:
            lines.append("".join(row))
        return "\n".join(lines)

    def is_valid_pos(self, x, y):
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            return self.grid[y][x] != WALL
        return False

    def move_guard(self):
        """Déplace le gardien aléatoirement vers une case vide proche (ou reste sur place)"""
        import random
        possible_moves = [(0,0), (1,0), (-1,0), (0,1), (0,-1)]
        random.shuffle(possible_moves)
        for dx, dy in possible_moves:
            nx, ny = self.guard_pos[0] + dx, self.guard_pos[1] + dy
            if self.is_valid_pos(nx, ny) and (nx, ny) != self.player_pos:
                self.grid[self.guard_pos[1]][self.guard_pos[0]] = EMPTY
                self.guard_pos = (nx, ny)
                self.grid[ny][nx] = GUARD
                break

    async def update_message(self):
        if self.message:
            await safe_edit(self.message, content=f"**Mini-jeu Évasion : Atteins la sortie {EXIT} sans te faire attraper !**\n\n{self.render_grid()}")

    async def end_game(self, won: bool):
        self.game_over = True
        if won:
            await safe_edit(self.message, content=f"🎉 Félicitations {self.ctx.author.mention}, tu as réussi à t'évader !\n\n{self.render_grid()}", view=None)
        else:
            await safe_edit(self.message, content=f"💥 Oh non {self.ctx.author.mention}, tu as été attrapé par le gardien !\n\n{self.render_grid()}", view=None)
        self.stop()

class MoveButton(discord.ui.Button):
    def __init__(self, emoji, move):
        super().__init__(style=discord.ButtonStyle.primary, emoji=emoji)
        self.move = move

    async def callback(self, interaction: discord.Interaction):
        view: EscapePrisonView = self.view
        if view.game_over:
            await interaction.response.send_message("Le jeu est terminé.", ephemeral=True)
            return

        if interaction.user != view.ctx.author:
            await interaction.response.send_message("Ce n'est pas ton jeu !", ephemeral=True)
            return

        # Calcul nouvelle position du joueur
        new_x = view.player_pos[0] + self.move[0]
        new_y = view.player_pos[1] + self.move[1]

        if not view.is_valid_pos(new_x, new_y):
            await interaction.response.send_message("Mouvement invalide (mur ou hors grille).", ephemeral=True)
            return

        # Mise à jour grille joueur
        view.grid[view.player_pos[1]][view.player_pos[0]] = EMPTY
        view.player_pos = (new_x, new_y)
        view.grid[new_y][new_x] = PLAYER

        # Déplacement gardien
        view.move_guard()

        # Vérification défaite
        if view.player_pos == view.guard_pos:
            await view.end_game(False)
            await interaction.response.defer()
            return

        # Vérification victoire
        if view.player_pos == EXIT_POS:
            await view.end_game(True)
            await interaction.response.defer()
            return

        await view.update_message()
        await interaction.response.defer()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class PrisonEscape(commands.Cog):
    """
    Commande !escape_prison — Mini-jeu d'évasion dans une grille
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="prisonbreak",
        help="Joue au mini-jeu d'évasion dans une prison.",
        description="Déplace-toi avec les boutons pour atteindre la sortie sans te faire attraper."
    )
    async def escape_prison(self, ctx: commands.Context):
        """Commande principale"""
        view = EscapePrisonView(ctx, self.bot)
        msg = await safe_send(ctx.channel, f"**Mini-jeu Évasion : Atteins la sortie {EXIT} sans te faire attraper !**\n\n{view.render_grid()}", view=view)
        view.message = msg

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = PrisonEscape(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
