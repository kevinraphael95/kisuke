# ────────────────────────────────────────────────────────────────────────────────
# 📌 mastermind2.py — Commande interactive !mastermind /mastermind
# Objectif : Jeu de logique Mastermind via boutons Discord avec difficulté et corruption
# Catégorie : Fun
# Accès : Public
# Cooldown : 1 utilisation / 10 secondes / utilisateur
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
# 🎨 Liste des couleurs utilisables
# ────────────────────────────────────────────────────────────────────────────────
COLORS = ["🟥", "🟦", "🟩", "🟨", "🟪", "🟧"]

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Vue principale du jeu Mastermind
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

        for color in COLORS:
            self.add_item(ColorButton(color, self))
        self.add_item(ValidateButton(self))
        self.add_item(ClearButton(self))

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎯 Mastermind — Trouve la combinaison !",
            description=(
                "🔴 : bonne couleur et bonne position\n"
                "⚪ : bonne couleur mais mauvaise position\n"
                "❌ : couleur absente"
            ),
            color=discord.Color.blue()
        )
        embed.add_field(
            name="🧪 Tentatives",
            value="\n".join(self.format_attempts()) or "Aucune tentative.",
            inline=False
        )
        embed.add_field(
            name="🧵 Proposition en cours",
            value="".join(self.current_guess) or "_Vide_",
            inline=False
        )
        embed.set_footer(text=f"Essais restants : {self.max_attempts - len(self.attempts)}")
        return embed

    def format_attempts(self):
        return [f"{''.join(guess)} → {''.join(feedback)}" for guess, feedback in self.attempts]

    def generate_feedback(self, guess):
        feedback = []
        code_copy = self.code[:]
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
            await safe_edit(self.message, embed=self.build_embed(), view=self)

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
        try:
            await interaction.response.defer()
        except discord.InteractionResponded:
            pass

    async def show_result(self, interaction: discord.Interaction, win: bool):
        self.stop()
        embed = discord.Embed(
            title="🎉 Gagné !" if win else "💀 Perdu !",
            description=f"La combinaison était : {' '.join(self.code)}",
            color=discord.Color.green() if win else discord.Color.red()
        )
        try:
            await interaction.response.edit_message(embed=embed, view=None)
        except discord.InteractionResponded:
            await interaction.edit_original_response(embed=embed, view=None)

# ────────────────────────────────────────────────────────────────────────────────
# 🔵 Boutons interactifs
# ────────────────────────────────────────────────────────────────────────────────
class ColorButton(Button):
    def __init__(self, color: str, view_ref: MastermindView):
        super().__init__(style=discord.ButtonStyle.secondary, emoji=color)
        self.color = color
        self.view_ref = view_ref

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await safe_respond(interaction, "⛔ Ce jeu ne t'appartient pas.", ephemeral=True)
        if len(self.view_ref.current_guess) >= self.view_ref.code_length:
            return await safe_respond(interaction, "❗ Nombre de couleurs atteint.", ephemeral=True)
        self.view_ref.current_guess.append(self.color)
        await self.view_ref.update_message()
        try:
            await interaction.response.defer()
        except discord.InteractionResponded:
            pass

class ClearButton(Button):
    def __init__(self, view_ref: MastermindView):
        super().__init__(emoji="🗑️", style=discord.ButtonStyle.danger)
        self.view_ref = view_ref

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await safe_respond(interaction, "⛔ Ce jeu ne t'appartient pas.", ephemeral=True)
        self.view_ref.current_guess.clear()
        await self.view_ref.update_message()
        try:
            await interaction.response.defer()
        except discord.InteractionResponded:
            pass

class ValidateButton(Button):
    def __init__(self, view_ref: MastermindView):
        super().__init__(emoji="✅", style=discord.ButtonStyle.success)
        self.view_ref = view_ref

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await safe_respond(interaction, "⛔ Ce jeu ne t'appartient pas.", ephemeral=True)
        if len(self.view_ref.current_guess) != self.view_ref.code_length:
            return await safe_respond(interaction, "⚠️ Nombre de couleurs insuffisant.", ephemeral=True)
        await self.view_ref.make_attempt(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Menu de sélection de difficulté
# ────────────────────────────────────────────────────────────────────────────────
class DifficultyView(View):
    def __init__(self, author: discord.User):
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
            return await safe_respond(interaction, "⛔ Ce menu ne t'appartient pas.", ephemeral=True)
        view = MastermindView(interaction.user, self.code_length, self.corruption)
        embed = view.build_embed()
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind(commands.Cog):
    """Mastermind interactif avec commandes prefix et slash."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="mastermind", aliases=["mm"], help="Jouer au Mastermind interactif.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def prefix_mastermind(self, ctx: commands.Context):
        view = DifficultyView(ctx.author)
        embed = discord.Embed(
            title="🎮 Choisis la difficulté du Mastermind",
            description="Clique sur un bouton ci-dessous :",
            color=discord.Color.orange()
        )
        await safe_send(ctx.channel, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="mastermind",
        description="Jouer au Mastermind interactif."
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def slash_mastermind(self, interaction: discord.Interaction):
        view = DifficultyView(interaction.user)
        embed = discord.Embed(
            title="🎮 Choisis la difficulté du Mastermind",
            description="Clique sur un bouton ci-dessous :",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Mastermind(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
