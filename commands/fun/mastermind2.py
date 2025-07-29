# ────────────────────────────────────────────────────────────────────────────────
# 📌 Mastermind2.py — Commande interactive !Mastermind2
# Objectif : Jouer au Mastermind2 contre le bot, via des boutons colorés
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
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Définition des couleurs disponibles
# ────────────────────────────────────────────────────────────────────────────────
COLORS = ["🟥", "🟦", "🟩", "🟨", "🟪", "🟧"]

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Vue interactive Mastermind2
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind2View2(View):
    def __init__(self, author: discord.User, code_length: int, corruption: bool):
        super().__init__(timeout=180)
        self.author = author
        self.code_length = code_length
        self.corruption = corruption
        self.max_attempts = code_length + 2
        self.code = [random.choice(COLORS) for _ in range(code_length)]
        self.attempts = []  # [(proposition, feedback)]
        self.current_guess = []
        self.message = None
        self.result_shown = False

        for color in COLORS:
            self.add_item(ColorButton(color, self))
        self.add_item(ValidateButton(self))
        self.add_item(ClearButton(self))

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎯 Mastermind2 — Trouve la combinaison !",
            description=(
                "🔴 : bonne couleur, bonne position\n"
                "⚪ : bonne couleur, mauvaise position\n"
                "❌ : couleur absente"
            ),
            color=discord.Color.blue()
        )
        embed.add_field(name="🧪 Tentatives", value="\n".join(self.format_attempts()) or "Aucune tentative.", inline=False)
        embed.add_field(name="🧵 Proposition en cours", value="".join(self.current_guess) or "_Vide_", inline=False)
        embed.set_footer(text=f"Tu as {self.max_attempts - len(self.attempts)} essais restants.")
        return embed

    def format_attempts(self):
        return [f"{''.join(guess)} → {''.join(feedback)}" for guess, feedback in self.attempts]

    def generate_feedback(self, guess):
        feedback = []
        code_copy = self.code[:]
        guess_copy = guess[:]

        matched_code = [False] * self.code_length
        matched_guess = [False] * self.code_length

        for i in range(self.code_length):
            if guess[i] == code_copy[i]:
                feedback.append("🔴")
                matched_code[i] = True
                matched_guess[i] = True
            else:
                feedback.append(None)

        for i in range(self.code_length):
            if feedback[i] is None:
                for j in range(self.code_length):
                    if not matched_code[j] and not matched_guess[i] and guess[i] == code_copy[j]:
                        feedback[i] = "⚪"
                        matched_code[j] = True
                        matched_guess[i] = True
                        break

        for i in range(self.code_length):
            if feedback[i] is None:
                feedback[i] = "❌"

        if self.corruption:
            feedback = [f if random.random() > 0.5 else "💀" for f in feedback]

        return feedback

    async def update_message(self):
        if self.message and not self.result_shown:
            embed = self.build_embed()
            await safe_edit(self.message, embed=embed, view=self)

    async def make_attempt(self, interaction: discord.Interaction):
        guess = self.current_guess[:]
        feedback = self.generate_feedback(guess)
        self.attempts.append((guess, feedback))
        self.current_guess.clear()

        if guess == self.code:
            self.result_shown = True
            await self.show_result(interaction, win=True)
            return

        if len(self.attempts) >= self.max_attempts:
            self.result_shown = True
            await self.show_result(interaction, win=False)
            return

        await self.update_message()
        await interaction.response.defer()

    async def show_result(self, interaction: discord.Interaction, win: bool):
        self.stop()
        result_embed = discord.Embed(
            title="🎉 Gagné !" if win else "💀 Perdu !",
            description=f"La combinaison était : {' '.join(self.code)}",
            color=discord.Color.green() if win else discord.Color.red()
        )
        await interaction.response.defer()
        await interaction.followup.send(embed=result_embed, ephemeral=False)

# ────────────────────────────────────────────────────────────────────────────────
# 🟦 Boutons de couleur
# ────────────────────────────────────────────────────────────────────────────────
class ColorButton(Button):
    def __init__(self, color: str, view: Mastermind2View2):
        self.color = color
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await interaction.response.send_message("⛔ Ce jeu ne t'appartient pas.", ephemeral=True)

        if len(self.view_ref.current_guess) >= self.view_ref.code_length:
            return await interaction.response.send_message("❗ Nombre de couleurs atteint.", ephemeral=True)

        self.view_ref.current_guess.append(self.color)
        await self.view_ref.update_message()
        await interaction.response.defer()

# ────────────────────────────────────────────────────────────────────────────────
# 🗑️ Bouton Reset
# ────────────────────────────────────────────────────────────────────────────────
class ClearButton(Button):
    def __init__(self, view: Mastermind2View2):
        super().__init__(emoji="🗑️", style=discord.ButtonStyle.danger)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await interaction.response.send_message("⛔ Ce jeu ne t'appartient pas.", ephemeral=True)

        self.view_ref.current_guess.clear()
        await self.view_ref.update_message()
        await interaction.response.defer()

# ────────────────────────────────────────────────────────────────────────────────
# ✅ Bouton Valider
# ────────────────────────────────────────────────────────────────────────────────
class ValidateButton(Button):
    def __init__(self, view: Mastermind2View2):
        super().__init__(emoji="✅", style=discord.ButtonStyle.success)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await interaction.response.send_message("⛔ Ce jeu ne t'appartient pas.", ephemeral=True)

        if len(self.view_ref.current_guess) != self.view_ref.code_length:
            return await interaction.response.send_message("⚠️ Nombre de couleurs insuffisant.", ephemeral=True)

        await self.view_ref.make_attempt(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue de sélection de difficulté
# ────────────────────────────────────────────────────────────────────────────────
class DifficultyView(View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

        self.add_item(DifficultyButton("Facile", 3, False))
        self.add_item(DifficultyButton("Normal", 4, False))
        self.add_item(DifficultyButton("Difficile", 5, False))
        self.add_item(DifficultyButton("Cauchemar", random.randint(8, 10), True))

class DifficultyButton(Button):
    def __init__(self, label, code_length, corruption):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.code_length = code_length
        self.corruption = corruption

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view.author:
            return await interaction.response.send_message("Ce menu ne t'est pas destiné.", ephemeral=True)

        view = Mastermind2View2(interaction.user, self.code_length, self.corruption)
        embed = view.build_embed()
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind2(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="Mastermind2", aliases=["mm2"], help="Jouer au Mastermind2.", description="Devine la combinaison de couleurs.")
    async def Mastermind2(self, ctx: commands.Context):
        view = DifficultyView(ctx.author)
        embed = discord.Embed(
            title="🎮 Choisis la difficulté du Mastermind2",
            description="Clique sur un bouton ci-dessous :",
            color=discord.Color.orange()
        )
        await safe_send(ctx, embed=embed, view=view)



# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Mastermind2(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
