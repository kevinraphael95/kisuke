# ────────────────────────────────────────────────────────────────────────────────
# 📌 mastermind2.py — Commande interactive /mastermind et !mastermind
# Objectif : Jeu de logique Mastermind via boutons Discord avec menu difficulté
# Catégorie : Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Couleurs disponibles
# ────────────────────────────────────────────────────────────────────────────────
COLORS = ["🟥", "🟦", "🟩", "🟨", "🟪", "🟧"]

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Views & Buttons Mastermind
# ────────────────────────────────────────────────────────────────────────────────
class MastermindView(View):
    def __init__(self, author: discord.User, code_length: int, corruption: bool):
        super().__init__(timeout=180)
        self.author = author
        self.code_length = code_length
        self.corruption = corruption
        self.max_attempts = code_length + 2
        self.code = [random.choice(COLORS) for _ in range(code_length)]
        self.attempts = []
        self.current_guess = []
        self.message = None
        self.result_shown = False

        # Ajout des boutons couleurs + valider/effacer
        for color in COLORS:
            self.add_item(ColorButton(color, self))
        self.add_item(ValidateButton(self))
        self.add_item(ClearButton(self))

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎯 Mastermind — Trouve la combinaison !",
            description="🔴 : bonne couleur & position\n⚪ : bonne couleur, mauvaise position\n❌ : couleur absente",
            color=discord.Color.blue()
        )
        embed.add_field(name="🧪 Tentatives", value="\n".join(self.format_attempts()) or "Aucune tentative.", inline=False)
        embed.add_field(name="🧵 Proposition en cours", value="".join(self.current_guess) or "_Vide_", inline=False)
        embed.set_footer(text=f"Essais restants : {self.max_attempts - len(self.attempts)}")
        return embed

    def format_attempts(self):
        return [f"{''.join(guess)} → {''.join(feedback)}" for guess, feedback in self.attempts]

    def generate_feedback(self, guess):
        feedback = [None] * self.code_length
        code_copy = self.code[:]
        matched_code = [False] * self.code_length
        matched_guess = [False] * self.code_length

        # 🔴 Couleurs à la bonne position
        for i in range(self.code_length):
            if guess[i] == code_copy[i]:
                feedback[i] = "🔴"
                matched_code[i] = True
                matched_guess[i] = True

        # ⚪ Couleurs correctes, mauvaise position
        for i in range(self.code_length):
            if feedback[i] is None:
                for j in range(self.code_length):
                    if not matched_code[j] and not matched_guess[i] and guess[i] == code_copy[j]:
                        feedback[i] = "⚪"
                        matched_code[j] = True
                        matched_guess[i] = True
                        break

        # ❌ Couleurs absentes
        for i in range(self.code_length):
            if feedback[i] is None:
                feedback[i] = "❌"

        # ☠️ Mode corruption
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
            await self.show_result(interaction, True)
            return

        if len(self.attempts) >= self.max_attempts:
            self.result_shown = True
            await self.show_result(interaction, False)
            return

        await self.update_message()
        await interaction.response.defer()

    async def show_result(self, interaction: discord.Interaction, win: bool):
        self.stop()
        embed = discord.Embed(
            title="🎉 Gagné !" if win else "💀 Perdu !",
            description=f"La combinaison était : {' '.join(self.code)}",
            color=discord.Color.green() if win else discord.Color.red()
        )
        await interaction.response.defer()
        await interaction.followup.send(embed=embed, ephemeral=False)

class ColorButton(Button):
    def __init__(self, color: str, view: MastermindView):
        super().__init__(style=discord.ButtonStyle.secondary, emoji=color)
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

class ClearButton(Button):
    def __init__(self, view: MastermindView):
        super().__init__(emoji="🗑️", style=discord.ButtonStyle.danger)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await interaction.response.send_message("⛔ Ce jeu ne t'appartient pas.", ephemeral=True)
        self.view_ref.current_guess.clear()
        await self.view_ref.update_message()
        await interaction.response.defer()

class ValidateButton(Button):
    def __init__(self, view: MastermindView):
        super().__init__(emoji="✅", style=discord.ButtonStyle.success)
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await interaction.response.send_message("⛔ Ce jeu ne t'appartient pas.", ephemeral=True)
        if len(self.view_ref.current_guess) != self.view_ref.code_length:
            return await interaction.response.send_message("⚠️ Nombre de couleurs insuffisant.", ephemeral=True)
        await self.view_ref.make_attempt(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Menu difficulté
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
            return await interaction.response.send_message("⛔ Ce menu ne t'est pas destiné.", ephemeral=True)
        view = MastermindView(interaction.user, self.code_length, self.corruption)
        embed = view.build_embed()
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind(commands.Cog):
    """
    Commande /mastermind et !mastermind — Jeu Mastermind interactif avec menu difficulté
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🔹 Commande SLASH
    @app_commands.command(name="mastermind", description="Jouer au Mastermind interactif.")
    async def slash_mastermind(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            view = DifficultyView(interaction.user)
            embed = discord.Embed(
                title="🎮 Choisis la difficulté du Mastermind",
                description="Clique sur un bouton ci-dessous :",
                color=discord.Color.orange()
            )
            await safe_send(interaction.channel, embed=embed, view=view)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /mastermind] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue lors du lancement du Mastermind.", ephemeral


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MastermindView(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
