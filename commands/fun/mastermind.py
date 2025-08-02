# ────────────────────────────────────────────────────────────────────────────────
# 📌 Mastermind2.py — Commande interactive !mastermind2
# Objectif : Jeu de logique Mastermind via des boutons Discord
# Catégorie : Jeux / Fun
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
# 🎨 Liste des couleurs utilisables (chaque couleur est un emoji carré)
# ────────────────────────────────────────────────────────────────────────────────
COLORS = ["🟥", "🟦", "🟩", "🟨", "🟪", "🟧"]

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Vue principale du jeu Mastermind2 (interface interactive)
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind2View2(View):
    def __init__(self, author: discord.User, code_length: int, corruption: bool):
        super().__init__(timeout=180)  # Temps d'inactivité avant expiration (180 sec)

        # 👤 Utilisateur ayant lancé le jeu (on bloque les autres)
        self.author = author

        # 🔢 Longueur du code à deviner (3 à 10 couleurs)
        self.code_length = code_length

        # ☠️ Mode "corruption" active des feedbacks aléatoires (💀)
        self.corruption = corruption

        # 📉 Nombre maximum d'essais autorisés (code_length + 2)
        self.max_attempts = code_length + 2

        # 🧠 Code secret généré aléatoirement
        self.code = [random.choice(COLORS) for _ in range(code_length)]

        # 📚 Historique des essais précédents (tuple : [proposition, feedback])
        self.attempts = []

        # 🧵 Proposition en cours (liste de couleurs sélectionnées)
        self.current_guess = []

        # 💬 Message contenant le jeu à modifier dynamiquement
        self.message = None

        # 🚩 Flag indiquant si le résultat (victoire/défaite) est déjà affiché
        self.result_shown = False

        # 🎨 Ajout dynamique des boutons de couleur, de validation et d'effacement
        for color in COLORS:
            self.add_item(ColorButton(color, self))
        self.add_item(ValidateButton(self))
        self.add_item(ClearButton(self))

    # 🔧 Génère dynamiquement l'embed contenant l'état du jeu
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
        embed.set_footer(text=f"Tu as {self.max_attempts - len(self.attempts)} essais restants.")
        return embed

    # 📄 Formate les tentatives passées pour affichage dans l'embed
    def format_attempts(self):
        return [f"{''.join(guess)} → {''.join(feedback)}" for guess, feedback in self.attempts]

    # 🧠 Génère un feedback pour une proposition donnée
    def generate_feedback(self, guess):
        feedback = []
        code_copy = self.code[:]
        matched_code = [False] * self.code_length
        matched_guess = [False] * self.code_length

        # 🔴 Étape 1 : Bonnes couleurs à la bonne position
        for i in range(self.code_length):
            if guess[i] == code_copy[i]:
                feedback.append("🔴")
                matched_code[i] = True
                matched_guess[i] = True
            else:
                feedback.append(None)  # Sera déterminé plus tard

        # ⚪ Étape 2 : Bonnes couleurs mais mauvaise position
        for i in range(self.code_length):
            if feedback[i] is None:
                for j in range(self.code_length):
                    if not matched_code[j] and not matched_guess[i] and guess[i] == code_copy[j]:
                        feedback[i] = "⚪"
                        matched_code[j] = True
                        matched_guess[i] = True
                        break

        # ❌ Étape 3 : Couleurs absentes
        for i in range(self.code_length):
            if feedback[i] is None:
                feedback[i] = "❌"

        # ☠️ Étape 4 : Corruption aléatoire des symboles (mode Cauchemar)
        if self.corruption:
            feedback = [f if random.random() > 0.5 else "💀" for f in feedback]

        return feedback

    # 🔄 Met à jour dynamiquement le message avec l'embed actuel
    async def update_message(self):
        if self.message and not self.result_shown:
            embed = self.build_embed()
            await safe_edit(self.message, embed=embed, view=self)

    # ✅ Gère la validation d'une proposition complète
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

    # 🏁 Affiche le résultat final (victoire ou défaite)
    async def show_result(self, interaction: discord.Interaction, win: bool):
        self.stop()  # Désactive la vue interactive
        result_embed = discord.Embed(
            title="🎉 Gagné !" if win else "💀 Perdu !",
            description=f"La combinaison était : {' '.join(self.code)}",
            color=discord.Color.green() if win else discord.Color.red()
        )
        await interaction.response.defer()
        await interaction.followup.send(embed=result_embed, ephemeral=False)

# ────────────────────────────────────────────────────────────────────────────────
# 🟦 Boutons de couleur (ajoute une couleur à la proposition)
# ────────────────────────────────────────────────────────────────────────────────
class ColorButton(Button):
    def __init__(self, color: str, view: Mastermind2View2):
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

# ────────────────────────────────────────────────────────────────────────────────
# 🗑️ Bouton pour réinitialiser la proposition en cours
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
# ✅ Bouton de validation d'une combinaison complète
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
# 🎛️ Menu de sélection de difficulté (vue initiale)
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
# 🧠 Cog principal : commande !mastermind2
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind2(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="mastermind", aliases=["mm"], help="Jouer au Mastermind.", description="Devine la combinaison de couleurs.")
    async def mastermind2(self, ctx: commands.Context):
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
