# ────────────────────────────────────────────────────────────────────────────────
# 📌 motus.py — Commande interactive /motus et !motus
# Objectif : Jeu du Motus avec proposition de mots et feedback coloré
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Modal, TextInput, Button
import random

# Utils sécurisés pour éviter erreurs 429
from utils.discord_utils import safe_send, safe_edit, safe_respond, safe_delete  

# ────────────────────────────────────────────────────────────────────────────────
# 🎲 Mots possibles pour le jeu
# ────────────────────────────────────────────────────────────────────────────────
WORDS = ["ARBRE", "MAISON", "PYTHON", "DISCORD", "BOT", "MOTUS"]

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Modal de saisie d’un mot
# ────────────────────────────────────────────────────────────────────────────────
class MotusModal(Modal):
    def __init__(self, parent_view, target_word):
        super().__init__(title="Propose un mot")
        self.parent_view = parent_view
        self.target_word = target_word
        self.word_input = TextInput(
            label="Mot",
            placeholder="Entre ton mot ici",
            required=True,
            max_length=len(target_word)
        )
        self.add_item(self.word_input)

    async def on_submit(self, interaction: discord.Interaction):
        guess = self.word_input.value.strip().upper()
        feedback = self.parent_view.create_feedback_line(guess, self.target_word)

        if guess == self.target_word:
            await safe_respond(interaction, f"🎉 Bravo ! Tu as trouvé le mot : **{self.target_word}**\n\n{feedback}")
            self.parent_view.stop()  # Fin du jeu
        else:
            await safe_respond(interaction, f"{feedback}\n\n❌ Ce n’est pas encore ça, réessaie !", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Bouton pour démarrer le jeu
# ────────────────────────────────────────────────────────────────────────────────
class MotusView(View):
    def __init__(self, target_word):
        super().__init__(timeout=180)
        self.target_word = target_word
        self.add_item(MotusButton(self))

    def create_feedback_line(self, guess: str, target: str) -> str:
        """Retourne une double ligne alignée : lettres 🇦 + couleurs en dessous"""

        def letter_to_emoji(c: str) -> str:
            if c.isalpha():
                return chr(0x1F1E6 + (ord(c.upper()) - ord('A')))  # 🇦
            return c.upper()

        letters = " ".join(letter_to_emoji(c) for c in guess)
        colors = []
        for i, c in enumerate(guess):
            if i < len(target) and c == target[i]:
                colors.append("🟩")
            elif c in target:
                colors.append("🟨")
            else:
                colors.append("⬛")
        return f"{letters}\n{' '.join(colors)}"

class MotusButton(Button):
    def __init__(self, parent_view: MotusView):
        super().__init__(label="Proposer un mot", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(MotusModal(self.parent_view, self.parent_view.target_word))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Motus(commands.Cog):
    """
    Commande /motus et !motus — Lance une partie de Motus
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Fonction interne
    async def _start_game(self, channel: discord.abc.Messageable):
        target_word = random.choice(WORDS)
        view = MotusView(target_word)
        await safe_send(channel, "🎯 Motus lancé ! Propose un mot :", view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="motus",
        description="Lance une partie de Motus."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_motus(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._start_game(interaction.channel)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /motus] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="motus")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_motus(self, ctx: commands.Context):
        try:
            await self._start_game(ctx.channel)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !motus] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Motus(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
