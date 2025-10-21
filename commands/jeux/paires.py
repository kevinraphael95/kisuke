# ────────────────────────────────────────────────────────────────────────────────
# 📌 memory_game.py — Jeu de paires (Memory) avec Discord
# Objectif : Jeu de memory temps réel avec emojis et thèmes
# Catégorie : Jeu
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
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
# 🎨 Thèmes possibles
# ────────────────────────────────────────────────────────────────────────────────
THEMES = {
    "fruits": ["🍎","🍌","🍇","🍓","🍍","🥭","🍉","🍑"],
    "animaux": ["🐶","🐱","🐭","🐰","🦊","🐼","🦁","🐸"],
    "couleurs": ["🔴","🟢","🔵","🟡","🟣","🟠","⚫","⚪"]
}

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Memory Game View
# ────────────────────────────────────────────────────────────────────────────────
class MemoryGameView(View):
    def __init__(self, ctx_or_interaction, theme="fruits", size=4):
        super().__init__(timeout=120)
        self.ctx_or_interaction = ctx_or_interaction
        self.size = size
        self.theme = theme if theme in THEMES else "fruits"
        self.emojis = THEMES[self.theme] * 2  # paires
        random.shuffle(self.emojis)
        self.board = [self.emojis[i*self.size:(i+1)*self.size] for i in range(self.size)]
        self.buttons = {}
        self.revealed = {}  # (r,c) -> emoji
        self.scores = {}    # user_id -> nombre de paires
        self.create_buttons()

    def create_buttons(self):
        for r in range(self.size):
            for c in range(self.size):
                btn = Button(label="❓", style=discord.ButtonStyle.secondary, row=r)
                btn.callback = self.make_callback(r, c)
                self.add_item(btn)
                self.buttons[(r,c)] = btn

    def make_callback(self, r, c):
        async def callback(interaction: discord.Interaction):
            if (r,c) in self.revealed:
                return  # déjà découvert
            # révéler le bouton
            emoji = self.board[r][c]
            btn = self.buttons[(r,c)]
            btn.label = emoji
            btn.style = discord.ButtonStyle.primary
            self.revealed[(r,c)] = emoji

            # vérifier si une paire est trouvée
            pairs = list(self.revealed.items())
            same_emoji_positions = [pos for pos,e in pairs if e == emoji]
            if len(same_emoji_positions) == 2:
                # paire trouvée
                user_id = interaction.user.id
                self.scores[user_id] = self.scores.get(user_id,0)+1
                for pos in same_emoji_positions:
                    self.buttons[pos].disabled = True
            await safe_edit(interaction.message, view=self)

        return callback

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class MemoryGame(commands.Cog):
    """Jeu de paires Memory temps réel — tout le monde peut jouer en même temps"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @discord.app_commands.command(
        name="memory",
        description="Jouer au Memory Game (paires)"
    )
    async def slash_memory(self, interaction: discord.Interaction, theme: str = "fruits"):
        await interaction.response.defer()
        view = MemoryGameView(interaction, theme=theme, size=4)
        view.message = await safe_send(interaction.channel, f"🧩 Memory Game — Thème : {theme}", view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="memory")
    async def prefix_memory(self, ctx: commands.Context, theme: str = "fruits"):
        view = MemoryGameView(ctx, theme=theme, size=4)
        view.message = await safe_send(ctx.channel, f"🧩 Memory Game — Thème : {theme}", view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MemoryGame(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
