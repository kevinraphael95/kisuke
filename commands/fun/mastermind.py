# ────────────────────────────────────────────────────────────────────────────────
# 📌 mastermind.py — Commande interactive !mastermind
# Objectif : Jouer à Mastermind contre le bot avec 6 couleurs d'emojis
# Catégorie : Autre
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import random

from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Constantes
# ────────────────────────────────────────────────────────────────────────────────
COLORS = ["🔴", "🟡", "🟢", "🔵", "🟣", "🟠"]
MAX_TURNS = 12
CODE_LENGTH = 4

# 🔴 = bonne couleur à la bonne place
# ⚪ = bonne couleur à la mauvaise place
# ❌ = couleur absente

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Classe de jeu Mastermind
# ────────────────────────────────────────────────────────────────────────────────
class MastermindGame:
    def __init__(self):
        self.secret_code = [random.choice(COLORS) for _ in range(CODE_LENGTH)]
        self.turns = []
        self.finished = False

    def evaluate_guess(self, guess):
        result = []
        code_copy = self.secret_code[:]
        guess_copy = guess[:]

        # 🔴 Exact match
        for i in range(CODE_LENGTH):
            if guess_copy[i] == code_copy[i]:
                result.append("🔴")
                code_copy[i] = guess_copy[i] = None

        # ⚪ Right color, wrong position
        for i in range(CODE_LENGTH):
            if guess_copy[i] and guess_copy[i] in code_copy:
                result.append("⚪")
                code_copy[code_copy.index(guess_copy[i])] = None
                guess_copy[i] = None

        # ❌ Absent color
        result += ["❌"] * (CODE_LENGTH - len(result))

        return result

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Vue interactive du Mastermind
# ────────────────────────────────────────────────────────────────────────────────
class MastermindView(View):
    def __init__(self, bot, game, interaction):
        super().__init__(timeout=300)
        self.bot = bot
        self.game = game
        self.interaction = interaction
        self.current_guess = []
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        for color in COLORS:
            self.add_item(ColorButton(color, self))
        if len(self.current_guess) > 0:
            self.add_item(Button(label="🗑️", style=discord.ButtonStyle.danger, custom_id="reset"))
        if len(self.current_guess) == CODE_LENGTH:
            self.add_item(Button(label="✅ Valider", style=discord.ButtonStyle.success, custom_id="validate"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.interaction.user.id

    async def on_timeout(self):
        await safe_edit(self.interaction.message, content="⏱️ Temps écoulé ! Partie annulée.", embed=None, view=None)

    async def handle_interaction(self, interaction: discord.Interaction):
        if interaction.data["custom_id"] == "reset":
            self.current_guess.clear()
        elif interaction.data["custom_id"] == "validate":
            result = self.game.evaluate_guess(self.current_guess)
            self.game.turns.append((self.current_guess.copy(), result))
            self.current_guess.clear()
            if result.count("🔴") == CODE_LENGTH:
                self.game.finished = True
                await self.show_result(victory=True)
                return
            elif len(self.game.turns) >= MAX_TURNS:
                self.game.finished = True
                await self.show_result(victory=False)
                return
        else:
            if len(self.current_guess) < CODE_LENGTH:
                self.current_guess.append(interaction.data["custom_id"])

        self.update_buttons()
        await safe_edit(interaction.message, embed=self.get_embed(), view=self)
        await interaction.response.defer()

    def get_embed(self):
        embed = discord.Embed(title="🎯 Mastermind - Trouve la combinaison !", color=discord.Color.purple())
        for i, (guess, result) in enumerate(self.game.turns):
            embed.add_field(name=f"Essai {i+1}", value=f"{' '.join(guess)} ➜ {' '.join(result)}", inline=False)
        if not self.game.finished:
            embed.add_field(name="Essai en cours", value="➤ " + " ".join(self.current_guess) + " _" * (CODE_LENGTH - len(self.current_guess)), inline=False)
        embed.set_footer(text=f"{len(self.game.turns)}/{MAX_TURNS} essais")
        return embed

    async def show_result(self, victory: bool):
        msg = "🏆 Bravo ! Tu as trouvé la combinaison secrète !" if victory else f"❌ Perdu ! La combinaison était : {' '.join(self.game.secret_code)}"
        await safe_edit(self.interaction.message, content=msg, embed=None, view=None)

class ColorButton(Button):
    def __init__(self, color, view: MastermindView):
        super().__init__(label=color, style=discord.ButtonStyle.secondary, emoji=color, custom_id=color)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        await self.view_ref.handle_interaction(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind(commands.Cog):
    """
    Commande !mastermind — Joue à Mastermind contre le bot
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="mastermind",
        help="Joue au jeu du Mastermind contre le bot.",
        description="Devine la combinaison secrète de 4 couleurs. 12 tentatives maximum."
    )
    async def mastermind(self, ctx: commands.Context):
        """Commande principale Mastermind."""
        try:
            game = MastermindGame()
            view = MastermindView(self.bot, game, ctx)
            await safe_send(ctx.channel, content=f"🎲 {ctx.author.mention} commence une partie de Mastermind !", embed=view.get_embed(), view=view)
        except Exception as e:
            print(f"[ERREUR mastermind] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors du lancement du jeu.")


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Mastermind(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
