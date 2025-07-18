# ────────────────────────────────────────────────────────────────────────────────
# 📌 puissance4.py — Commande interactive !couleur
# Objectif : Afficher une couleur aléatoire avec ses codes HEX et RGB dans un embed Discord
# Catégorie : 🎨 Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import random
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Classe de jeu Puissance 4
# ────────────────────────────────────────────────────────────────────────────────
ROWS = 6
COLUMNS = 7
EMPTY = "⚪"
PLAYER_TOKENS = ["🔴", "🟡"]

class Puissance4Game:
    def __init__(self, player1, player2, vs_bot=False):
        self.board = [[EMPTY for _ in range(COLUMNS)] for _ in range(ROWS)]
        self.players = [player1, player2]
        self.current_turn = 0
        self.vs_bot = vs_bot
        self.game_over = False

    def drop_piece(self, col):
        for row in reversed(range(ROWS)):
            if self.board[row][col] == EMPTY:
                self.board[row][col] = PLAYER_TOKENS[self.current_turn]
                return row
        return None

    def is_valid_move(self, col):
        return self.board[0][col] == EMPTY

    def check_victory(self, row, col):
        token = PLAYER_TOKENS[self.current_turn]
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for dx, dy in directions:
            count = 1
            for dir in [1, -1]:
                for i in range(1, 4):
                    nx, ny = col + dir*i*dx, row + dir*i*dy
                    if 0 <= nx < COLUMNS and 0 <= ny < ROWS and self.board[ny][nx] == token:
                        count += 1
                    else:
                        break
            if count >= 4:
                return True
        return False

    def board_to_string(self):
        return "\n".join("".join(row) for row in self.board) + "\n" + "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Vue interactive
# ────────────────────────────────────────────────────────────────────────────────
class Puissance4View(View):
    def __init__(self, bot, ctx, player1, player2, vs_bot):
        super().__init__(timeout=180)
        self.bot = bot
        self.ctx = ctx
        self.game = Puissance4Game(player1, player2, vs_bot)
        self.message = None

        for i in range(COLUMNS):
            self.add_item(ColButton(i))

    async def start(self):
        content = f"🎮 **Puissance 4** — {self.game.players[0].mention} vs {self.game.players[1].mention}\n" \
                  f"Tour de {self.game.players[self.game.current_turn].mention} ({PLAYER_TOKENS[self.game.current_turn]})"
        self.message = await safe_send(self.ctx.channel, content, view=self)

    async def update_board(self, interaction: discord.Interaction, col: int):
        if self.game.game_over:
            return

        current_player = self.game.players[self.game.current_turn]

        if interaction.user != current_player:
            await interaction.response.defer()
            return

        if not self.game.is_valid_move(col):
            await interaction.response.send_message("❌ Colonne pleine !", ephemeral=True)
            return

        row = self.game.drop_piece(col)
        if self.game.check_victory(row, col):
            self.game.game_over = True
            await safe_edit(self.message, content=f"🎉 Victoire de {current_player.mention} !\n{self.game.board_to_string()}", view=None)
            return

        if all(not self.game.is_valid_move(c) for c in range(COLUMNS)):
            self.game.game_over = True
            await safe_edit(self.message, content=f"🤝 Match nul !\n{self.game.board_to_string()}", view=None)
            return

        self.game.current_turn = 1 - self.game.current_turn
        next_player = self.game.players[self.game.current_turn]
        content = f"🎮 **Puissance 4** — {self.game.players[0].mention} vs {self.game.players[1].mention}\n" \
                  f"Tour de {next_player.mention} ({PLAYER_TOKENS[self.game.current_turn]})\n{self.game.board_to_string()}"
        await safe_edit(self.message, content=content)

        # Si c'est le tour du bot
        if self.game.vs_bot and next_player.bot:
            await self.bot_move()

    async def bot_move(self):
        await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=1))
        valid_cols = [i for i in range(COLUMNS) if self.game.is_valid_move(i)]
        col = random.choice(valid_cols)
        row = self.game.drop_piece(col)

        if self.game.check_victory(row, col):
            self.game.game_over = True
            await safe_edit(self.message, content=f"🤖 Le bot a gagné !\n{self.game.board_to_string()}", view=None)
            return

        if all(not self.game.is_valid_move(c) for c in range(COLUMNS)):
            self.game.game_over = True
            await safe_edit(self.message, content=f"🤝 Match nul !\n{self.game.board_to_string()}", view=None)
            return

        self.game.current_turn = 0
        content = f"🎮 **Puissance 4** — {self.game.players[0].mention} vs {self.game.players[1].mention}\n" \
                  f"Tour de {self.game.players[0].mention} ({PLAYER_TOKENS[0]})\n{self.game.board_to_string()}"
        await safe_edit(self.message, content=content)

class ColButton(Button):
    def __init__(self, col):
        super().__init__(style=discord.ButtonStyle.primary, label=str(col + 1), row=col // 4)
        self.col = col

    async def callback(self, interaction: discord.Interaction):
        await self.view.update_board(interaction, self.col)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Puissance4(commands.Cog):
    """
    Commande !puissance4 — Joue au Puissance 4 contre un autre joueur ou contre le bot.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="puissance4",
        help="Joue à Puissance 4 contre un ami ou contre le bot.",
        description="Utilisation : !puissance4 [@joueur]"
    )
    async def puissance4(self, ctx: commands.Context, opponent: discord.Member = None):
        """Lance une partie de Puissance 4."""
        try:
            if opponent and opponent.bot and opponent != ctx.guild.me:
                await safe_send(ctx.channel, "❌ Tu ne peux pas jouer contre d'autres bots.")
                return

            player2 = opponent or ctx.guild.me
            vs_bot = player2 == ctx.guild.me

            view = Puissance4View(self.bot, ctx, ctx.author, player2, vs_bot)
            await view.start()

        except Exception as e:
            print(f"[ERREUR puissance4] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors du lancement de la partie.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Puissance4(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
