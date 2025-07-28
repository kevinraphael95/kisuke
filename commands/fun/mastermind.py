# ────────────────────────────────────────────────────────────────────────────────
# 🧠 mastermind.py — Commande interactive !mastermind
# Objectif : Deviner une combinaison secrète de 4 couleurs avec indices
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
# 🎨 Constantes du jeu
# ────────────────────────────────────────────────────────────────────────────────
COLORS = ["🔴", "🟡", "🟢", "🔵", "🟣", "🟠"]
MAX_ATTEMPTS = 12

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Vue du Mastermind
# ────────────────────────────────────────────────────────────────────────────────
class MastermindView(View):
    def __init__(self, bot, author: discord.User):
        super().__init__(timeout=180)
        self.bot = bot
        self.author = author
        self.code = [random.choice(COLORS) for _ in range(4)]
        self.current_guess = []
        self.attempts = []
        self.finished = False
        for emoji in COLORS:
            self.add_item(ColorButton(self, emoji))
        self.add_item(ValidateButton(self))
        self.add_item(ClearButton(self))

    def format_attempts(self):
        lines = []
        for guess, result in self.attempts:
            line = f"{' '.join(guess)} ➜ {' '.join(result)}"
            lines.append(line)
        return "\n".join(lines) if lines else "Aucune tentative encore."

    def compute_feedback(self, guess):
        result = []
        code_copy = self.code.copy()
        guess_copy = guess.copy()

        # 🔴 Bon endroit
        for i in range(4):
            if guess[i] == code_copy[i]:
                result.append("🔴")
                code_copy[i] = None
                guess_copy[i] = None

        # ⚪ Mauvais endroit
        for i in range(4):
            if guess_copy[i] and guess_copy[i] in code_copy:
                result.append("⚪")
                code_copy[code_copy.index(guess_copy[i])] = None

        # ❌ Mauvaise couleur
        result += ["❌"] * (4 - len(result))
        return result

    async def update_message(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎯 Mastermind",
            description=f"Devine la combinaison secrète de 4 couleurs parmi :\n{' '.join(COLORS)}",
            color=discord.Color.dark_purple()
        )
        embed.add_field(name="Tes tentatives", value=self.format_attempts(), inline=False)
        embed.set_footer(text=f"Essai {len(self.attempts)}/{MAX_ATTEMPTS}")
        await safe_edit(interaction.message, embed=embed, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🟦 Bouton de couleur
# ────────────────────────────────────────────────────────────────────────────────
class ColorButton(Button):
    def __init__(self, parent_view: MastermindView, emoji: str):
        super().__init__(emoji=emoji, style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view
        self.emoji_used = emoji

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent_view.author:
            return await safe_respond(interaction, "❌ Ce jeu ne t'appartient pas.", ephemeral=True)
        if self.parent_view.finished:
            return
        if len(self.parent_view.current_guess) >= 4:
            return await safe_respond(interaction, "⚠️ Tu as déjà choisi 4 couleurs.", ephemeral=True)
        self.parent_view.current_guess.append(self.emoji_used)
        await self.parent_view.update_message(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# ✅ Bouton valider
# ────────────────────────────────────────────────────────────────────────────────
class ValidateButton(Button):
    def __init__(self, parent_view: MastermindView):
        super().__init__(label="Valider", style=discord.ButtonStyle.success)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent_view.author:
            return await safe_respond(interaction, "❌ Ce jeu ne t'appartient pas.", ephemeral=True)
        if self.parent_view.finished:
            return
        if len(self.parent_view.current_guess) != 4:
            return await safe_respond(interaction, "⚠️ Il te faut 4 couleurs.", ephemeral=True)

        result = self.parent_view.compute_feedback(self.parent_view.current_guess)
        self.parent_view.attempts.append((self.parent_view.current_guess.copy(), result))
        self.parent_view.current_guess = []

        if result == ["🔴"] * 4:
            self.parent_view.finished = True
            await safe_edit(interaction.message, embed=discord.Embed(
                title="🏆 Bravo !",
                description=f"Tu as trouvé la combinaison secrète !\n{' '.join(self.parent_view.code)}",
                color=discord.Color.green()
            ), view=None)
        elif len(self.parent_view.attempts) >= MAX_ATTEMPTS:
            self.parent_view.finished = True
            await safe_edit(interaction.message, embed=discord.Embed(
                title="💀 Perdu...",
                description=f"Tu as épuisé tes essais.\nLa bonne combinaison était : {' '.join(self.parent_view.code)}",
                color=discord.Color.red()
            ), view=None)
        else:
            await self.parent_view.update_message(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🔄 Bouton effacer
# ────────────────────────────────────────────────────────────────────────────────
class ClearButton(Button):
    def __init__(self, parent_view: MastermindView):
        super().__init__(label="Effacer", style=discord.ButtonStyle.danger)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent_view.author:
            return await safe_respond(interaction, "❌ Ce jeu ne t'appartient pas.", ephemeral=True)
        if self.parent_view.finished:
            return
        self.parent_view.current_guess = []
        await self.parent_view.update_message(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind(commands.Cog):
    """
    Commande !mastermind — Devine une combinaison secrète avec des emojis
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="mastermind",
        help="Joue au Mastermind contre le bot !",
        description="Jeu de Mastermind classique en emojis (🔴🟡🟢🔵🟣🟠)."
    )
    async def mastermind(self, ctx: commands.Context):
        """Commande principale pour jouer au Mastermind."""
        try:
            view = MastermindView(self.bot, ctx.author)
            embed = discord.Embed(
                title="🎯 Mastermind",
                description=f"Devine la combinaison secrète de 4 couleurs parmi :\n{' '.join(COLORS)}",
                color=discord.Color.dark_purple()
            )
            embed.set_footer(text=f"Essai 0/{MAX_ATTEMPTS}")
            await safe_send(ctx.channel, embed=embed, view=view)
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
