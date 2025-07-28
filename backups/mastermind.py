# ────────────────────────────────────────────────────────────────────────────────
# 📌 mastermind.py — Commande interactive !mastermind
# Objectif : Jouer au Mastermind contre le bot, via des boutons colorés
# Catégorie : Jeux
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
# 🎨 Définition des couleurs disponibles
# ────────────────────────────────────────────────────────────────────────────────
COLORS = ["🟥", "🟦", "🟩", "🟨", "🟪", "🟧"]
MAX_ATTEMPTS = 12
CODE_LENGTH = 4

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Vue interactive Mastermind
# ────────────────────────────────────────────────────────────────────────────────
class MastermindView(View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=180)
        self.author = author
        self.code = [random.choice(COLORS) for _ in range(CODE_LENGTH)]
        self.attempts = []  # [(proposition, feedback)]
        self.current_guess = []
        self.message = None

        for color in COLORS:
            self.add_item(ColorButton(color, self))
        self.add_item(ValidateButton(self))
        self.add_item(ClearButton(self))

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(title="🎯 Mastermind — Trouve la combinaison !", color=discord.Color.blue())
        embed.add_field(name="🧪 Tentatives", value="\n".join(self.format_attempts()) or "Aucune tentative.", inline=False)
        embed.add_field(name="🧵 Proposition en cours", value="".join(self.current_guess) or "_Vide_", inline=False)
        embed.set_footer(text=f"Tu as {MAX_ATTEMPTS - len(self.attempts)} essais restants.")
        return embed

    def format_attempts(self):
        return [f"{''.join(guess)} → {''.join(feedback)}" for guess, feedback in self.attempts]

    def generate_feedback(self, guess):
        feedback = []
        code_copy = self.code[:]
        guess_copy = guess[:]

        # 🔴 bonne couleur, bonne position
        for i in range(CODE_LENGTH):
            if guess[i] == code_copy[i]:
                feedback.append("🔴")
                guess_copy[i] = None
                code_copy[i] = None

        # ⚪ bonne couleur, mauvaise position
        for i in range(CODE_LENGTH):
            if guess_copy[i] and guess_copy[i] in code_copy:
                feedback.append("⚪")
                code_copy[code_copy.index(guess_copy[i])] = None
                guess_copy[i] = None

        # ❌ couleur absente
        feedback += ["❌"] * (CODE_LENGTH - len(feedback))
        return feedback

    async def update_message(self):
        if self.message:
            embed = self.build_embed()
            await safe_edit(self.message, embed=embed, view=self)

    async def make_attempt(self, interaction: discord.Interaction):
        guess = self.current_guess[:]
        feedback = self.generate_feedback(guess)
        self.attempts.append((guess, feedback))
        self.current_guess.clear()

        if guess == self.code:
            embed = discord.Embed(title="🎉 Gagné !", description=f"Tu as trouvé la combinaison : {' '.join(self.code)}", color=discord.Color.green())
            self.stop()
            await safe_edit(self.message, embed=embed, view=None)
            return

        if len(self.attempts) >= MAX_ATTEMPTS:
            embed = discord.Embed(title="💀 Perdu !", description=f"La combinaison était : {' '.join(self.code)}", color=discord.Color.red())
            self.stop()
            await safe_edit(self.message, embed=embed, view=None)
            return

        await self.update_message()

# ────────────────────────────────────────────────────────────────────────────────
# 🟦 Boutons de couleur
# ────────────────────────────────────────────────────────────────────────────────
class ColorButton(Button):
    def __init__(self, color: str, view: MastermindView):
        super().__init__(label=color, style=discord.ButtonStyle.secondary, emoji=color)
        self.color = color
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await interaction.response.send_message("⛔ Ce jeu ne t'appartient pas.", ephemeral=True)

        if len(self.view_ref.current_guess) >= CODE_LENGTH:
            return await interaction.response.send_message("❗ Tu as déjà sélectionné 4 couleurs.", ephemeral=True)

        self.view_ref.current_guess.append(self.color)
        await self.view_ref.update_message()

# ────────────────────────────────────────────────────────────────────────────────
# 🗑️ Bouton Reset
# ────────────────────────────────────────────────────────────────────────────────
class ClearButton(Button):
    def __init__(self, view: MastermindView):
        super().__init__(emoji="🗑️", style=discord.ButtonStyle.danger)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await interaction.response.send_message("⛔ Ce jeu ne t'appartient pas.", ephemeral=True)

        self.view_ref.current_guess.clear()
        await self.view_ref.update_message()

# ────────────────────────────────────────────────────────────────────────────────
# ✅ Bouton Valider
# ────────────────────────────────────────────────────────────────────────────────
class ValidateButton(Button):
    def __init__(self, view: MastermindView):
        super().__init__(emoji="✅", style=discord.ButtonStyle.success)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await interaction.response.send_message("⛔ Ce jeu ne t'appartient pas.", ephemeral=True)

        if len(self.view_ref.current_guess) != CODE_LENGTH:
            return await interaction.response.send_message("⚠️ Il faut choisir 4 couleurs pour valider.", ephemeral=True)

        await self.view_ref.make_attempt(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind(commands.Cog):
    """
    Commande !mastermind — Devine la combinaison de couleurs du bot
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="mastermind",
        help="Jouer au jeu du Mastermind contre le bot.",
        description="Devine la combinaison secrète de 4 couleurs parmi 6."
    )
    async def mastermind(self, ctx: commands.Context):
        """Commande principale pour lancer Mastermind."""
        view = MastermindView(ctx.author)
        embed = view.build_embed()
        msg = await safe_send(ctx, embed=embed, view=view)
        view.message = msg



# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Mastermind(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
