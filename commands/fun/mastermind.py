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
from discord.ui import View, Button, Select
import random
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Définition des constantes et couleurs
# ────────────────────────────────────────────────────────────────────────────────
COLORS = ["🟥", "🟦", "🟩", "🟨", "🟪", "🟧"]
MAX_ATTEMPTS = 12

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Vue interactive Mastermind (avec menu de difficulté)
# ────────────────────────────────────────────────────────────────────────────────
class MastermindView(View):
    def __init__(self, author: discord.User, code_length: int, corrupted: bool = False):
        super().__init__(timeout=180)
        self.author = author
        self.code_length = code_length
        self.corrupted = corrupted
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
                "🔴 : bonne couleur, bonne position\n"
                "⚪ : bonne couleur, mauvaise position\n"
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
        embed.set_footer(text=f"Tu as {MAX_ATTEMPTS - len(self.attempts)} essais restants.")
        return embed

    def format_attempts(self):
        lines = []
        for guess, feedback in self.attempts:
            if self.corrupted:
                corrupted_feedback = [symbol if random.random() > 0.5 else "💀" for symbol in feedback]
                lines.append(f"{''.join(guess)} → {''.join(corrupted_feedback)}")
            else:
                lines.append(f"{''.join(guess)} → {''.join(feedback)}")
        return lines

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

        if len(self.attempts) >= MAX_ATTEMPTS:
            self.result_shown = True
            await self.show_result(interaction, win=False)
            return

        await self.update_message()
        await interaction.response.defer()

    async def show_result(self, interaction: discord.Interaction, win: bool):
        self.result_shown = True
        for item in self.children:
            item.disabled = True
        embed = self.build_embed()
        result_embed = discord.Embed(
            title="🎉 Gagné !" if win else "💀 Perdu !",
            description=f"La combinaison était : {' '.join(self.code)}",
            color=discord.Color.green() if win else discord.Color.red()
        )
        await safe_edit(self.message, embed=embed, view=self)
        await interaction.followup.send(embed=result_embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔳 Boutons de couleur
# ────────────────────────────────────────────────────────────────────────────────
class ColorButton(Button):
    def __init__(self, color: str, view: MastermindView):
        super().__init__(style=discord.ButtonStyle.secondary, emoji=color)
        self.color = color
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.author:
            return await interaction.response.send_message("⛔ Ce jeu ne t'appartient pas.", ephemeral=True)

        if len(self.view_ref.current_guess) >= self.view_ref.code_length:
            return await interaction.response.send_message("❗ Tu as déjà sélectionné assez de couleurs.", ephemeral=True)

        self.view_ref.current_guess.append(self.color)
        await self.view_ref.update_message()
        await interaction.response.defer()

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
        await interaction.response.defer()

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

        if len(self.view_ref.current_guess) != self.view_ref.code_length:
            return await interaction.response.send_message("⚠️ Tu dois entrer une combinaison complète.", ephemeral=True)

        await self.view_ref.make_attempt(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal avec menu de difficulté
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="mastermind", aliases=["mm"], help="Jouer au Mastermind")
    async def mastermind(self, ctx: commands.Context):
        options = [
            discord.SelectOption(label="Facile", description="3 couleurs", value="3"),
            discord.SelectOption(label="Normal", description="4 couleurs", value="4"),
            discord.SelectOption(label="Difficile", description="5 couleurs", value="5"),
            discord.SelectOption(label="Cauchemar", description="8 à 10 couleurs, feedback corrompu", value="cauchemar")
        ]

        async def select_callback(interaction: discord.Interaction):
            if interaction.user != ctx.author:
                return await interaction.response.send_message("Ce menu ne t'est pas destiné.", ephemeral=True)

            value = interaction.data["values"][0]
            if value == "cauchemar":
                code_length = random.randint(8, 10)
                corrupted = True
            else:
                code_length = int(value)
                corrupted = False

            view = MastermindView(ctx.author, code_length, corrupted)
            embed = view.build_embed()
            msg = await safe_send(ctx, embed=embed, view=view)
            view.message = msg

        select = Select(placeholder="Choisis la difficulté", options=options)
        select.callback = select_callback
        view = View()
        view.add_item(select)

        await ctx.send("Choisis ton niveau de difficulté :", view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Mastermind(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
