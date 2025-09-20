# ────────────────────────────────────────────────────────────────────────────────
# 📌 mastermind.py — Commande interactive !mastermind /mastermind
# Objectif : Jeu de logique Mastermind via boutons Discord avec mode solo/multi
# Catégorie : Jeux
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
from utils.discord_utils import safe_send, safe_edit, safe_respond, safe_defer

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Liste des couleurs utilisables
# ────────────────────────────────────────────────────────────────────────────────
COLORS = ["🟥", "🟦", "🟩", "🟨", "🟪", "🟧"]

# ────────────────────────────────────────────────────────────────────────────────
# 🟢 Liste des difficultés
# ────────────────────────────────────────────────────────────────────────────────
DIFFICULTIES = [
    {"label": "Facile", "code_length": 3, "corruption": False},
    {"label": "Normal", "code_length": 4, "corruption": False},
    {"label": "Difficile", "code_length": 5, "corruption": False},
    {"label": "Cauchemar", "code_length": random.randint(8, 10), "corruption": True},
]

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Vue principale du jeu Mastermind
# ────────────────────────────────────────────────────────────────────────────────
class MastermindView(View):
    def __init__(self, author: discord.User | None, code_length: int, corruption: bool):
        """
        author = None → mode multi
        author = discord.User → mode solo
        """
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

        # Boutons couleurs
        for color in COLORS:
            self.add_item(MMButton("color", color, self))
        # Boutons d'action
        self.add_item(MMButton("validate", "✅", self))
        self.add_item(MMButton("clear", "🗑️", self))

    # ────────────────────────────────────────────────────────────
    def build_embed(self) -> discord.Embed:
        mode_text = "Multi" if self.author is None else "Solo"
        embed = discord.Embed(
            title=f"🎯 Mastermind - mode {mode_text}",
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

    # ────────────────────────────────────────────────────────────
    def format_attempts(self):
        return [f"{''.join(guess)}\n{''.join(feedback)}" for guess, feedback in self.attempts]

    # ────────────────────────────────────────────────────────────
    def generate_feedback(self, guess):
        feedback = []
        code_copy = self.code[:]
        matched_code = [False] * self.code_length
        matched_guess = [False] * self.code_length

        # 🔴 bonne position
        for i in range(self.code_length):
            if guess[i] == code_copy[i]:
                feedback.append("🔴")
                matched_code[i] = True
                matched_guess[i] = True
            else:
                feedback.append(None)
        # ⚪ bonne couleur mauvaise position
        for i in range(self.code_length):
            if feedback[i] is None:
                for j in range(self.code_length):
                    if not matched_code[j] and not matched_guess[i] and guess[i] == code_copy[j]:
                        feedback[i] = "⚪"
                        matched_code[j] = True
                        matched_guess[i] = True
                        break
        # ❌ couleur absente
        for i in range(self.code_length):
            if feedback[i] is None:
                feedback[i] = "❌"
        # 💀 corruption
        if self.corruption:
            feedback = [f if random.random() > 0.20 else "💀" for f in feedback]
        return feedback

    # ────────────────────────────────────────────────────────────
    async def update_message(self):
        if self.message and not self.result_shown:
            await safe_edit(self.message, embed=self.build_embed(), view=self)

    # ────────────────────────────────────────────────────────────
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
        await safe_defer(interaction)

    # ────────────────────────────────────────────────────────────
    async def show_result(self, interaction: discord.Interaction, win: bool):
        self.stop()
        for item in self.children:
            item.disabled = True
        embed = self.build_embed()
        embed.add_field(
            name="🏁 Résultat",
            value=f"**{'Gagné ! 🎉' if win else 'Perdu ! 💀'}**\n"
                  f"La combinaison était : {' '.join(self.code)}",
            inline=False
        )
        embed.color = discord.Color.green() if win else discord.Color.red()
        try:
            await safe_edit(interaction.message, embed=embed, view=self)
        except Exception:
            pass

# ────────────────────────────────────────────────────────────────────────────────
# 🔵 Bouton générique Mastermind
# ────────────────────────────────────────────────────────────────────────────────
class MMButton(Button):
    def __init__(self, button_type: str, value: str, view_ref: MastermindView | None = None, author: discord.User | None = None):
        """
        button_type: color / validate / clear / difficulty
        value: emoji ou label
        view_ref: référence MastermindView (pour color/validate/clear)
        author: pour DifficultyButton
        """
        style = discord.ButtonStyle.secondary
        if button_type == "validate":
            style = discord.ButtonStyle.success
        elif button_type == "clear":
            style = discord.ButtonStyle.danger
        elif button_type == "difficulty":
            style = discord.ButtonStyle.primary

        super().__init__(label=value if button_type == "difficulty" else None,
                         emoji=value if button_type != "difficulty" else None,
                         style=style)
        self.button_type = button_type
        self.view_ref = view_ref
        self.author = author
        self.value = value

    async def callback(self, interaction: discord.Interaction):
        await safe_defer(interaction)
        # ── Vérification utilisateur mode solo
        if self.view_ref and self.view_ref.author and interaction.user != self.view_ref.author:
            return await safe_respond(interaction, "⛔ Ce jeu ne t'appartient pas.", ephemeral=True)

        # ── Actions selon type
        if self.button_type == "color":
            if len(self.view_ref.current_guess) >= self.view_ref.code_length:
                return await safe_respond(interaction, "❗ Nombre de couleurs atteint.", ephemeral=True)
            self.view_ref.current_guess.append(self.value)
            await self.view_ref.update_message()

        elif self.button_type == "clear":
            self.view_ref.current_guess.clear()
            await self.view_ref.update_message()

        elif self.button_type == "validate":
            if len(self.view_ref.current_guess) != self.view_ref.code_length:
                return await safe_respond(interaction, "⚠️ Nombre de couleurs insuffisant.", ephemeral=True)
            await self.view_ref.make_attempt(interaction)

        elif self.button_type == "difficulty":
            view = MastermindView(self.author, self.value["code_length"], self.value["corruption"])
            embed = view.build_embed()
            await interaction.response.edit_message(embed=embed, view=view)
            view.message = interaction.message

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Menu de sélection de difficulté
# ────────────────────────────────────────────────────────────────────────────────
class DifficultyView(View):
    def __init__(self, author: discord.User | None, mode: str = "solo"):
        """
        author = utilisateur qui lance le jeu
        mode = "solo" ou "multi"
        """
        super().__init__(timeout=60)
        self.author = author if mode.lower() == "solo" else None
        for diff in DIFFICULTIES:
            self.add_item(MMButton("difficulty", diff, author=self.author))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind(commands.Cog):
    """Mastermind interactif avec commandes prefix et slash."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────
    @commands.command(name="mastermind", aliases=["mm"], help="Jouer au Mastermind interactif.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def prefix_mastermind(self, ctx: commands.Context, mode: str = "solo"):
        view = DifficultyView(ctx.author, mode)
        embed = discord.Embed(
            title=f"🎮 Choisis la difficulté — mode {'Multi' if mode.lower() != 'solo' else 'Solo'}",
            description="Clique sur un bouton ci-dessous :",
            color=discord.Color.orange()
        )
        await safe_send(ctx.channel, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────
    @app_commands.command(
        name="mastermind",
        description="Jouer au Mastermind interactif."
    )
    @app_commands.describe(mode="Mode de jeu : solo ou multi")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def slash_mastermind(self, interaction: discord.Interaction, mode: str = "solo"):
        view = DifficultyView(interaction.user, mode)
        embed = discord.Embed(
            title=f"🎮 Choisis la difficulté — mode {'Multi' if mode.lower() != 'solo' else 'Solo'}",
            description="Clique sur un bouton ci-dessous :",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=view)

# ────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Mastermind(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
