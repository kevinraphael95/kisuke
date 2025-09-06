# ────────────────────────────────────────────────────────────────────────────────
# 📌 motus.py — Commande interactive /motus et !motus
# Objectif : Jeu du Motus avec embed, tentatives limitées et feedback coloré
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
import aiohttp   # 👈 pour l’API
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🌐 Fonction pour récupérer un mot français aléatoire
# ────────────────────────────────────────────────────────────────────────────────
async def get_random_french_word(length: int | None = None) -> str:
    """Récupère un mot français aléatoire depuis l'API trouve-mot.fr"""
    url = "https://trouve-mot.fr/api/random"
    if length:
        url += f"?size={length}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return data[0]["name"].upper()
    except Exception as e:
        print(f"[ERREUR API Motus] {e}")

    # fallback si l’API échoue
    return "PYTHON"

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Modal pour proposer un mot
# ────────────────────────────────────────────────────────────────────────────────
class MotusModal(Modal):
    def __init__(self, parent_view):
        super().__init__(title="Propose un mot")
        self.parent_view = parent_view
        self.word_input = TextInput(
            label="Mot",
            placeholder=f"Mot de {len(self.parent_view.target_word)} lettres",
            required=True,
            max_length=len(self.parent_view.target_word),
            min_length=len(self.parent_view.target_word)
        )
        self.add_item(self.word_input)

    async def on_submit(self, interaction: discord.Interaction):
        guess = self.word_input.value.strip().upper()
        await self.parent_view.process_guess(interaction, guess)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue principale avec bouton
# ────────────────────────────────────────────────────────────────────────────────
class MotusView(View):
    def __init__(self, target_word: str, max_attempts: int = 6):
        super().__init__(timeout=180)
        self.target_word = target_word
        self.max_attempts = max_attempts
        self.attempts = []
        self.message = None
        self.finished = False
        self.add_item(MotusButton(self))

    def create_feedback_line(self, guess: str) -> str:
        """Retourne les deux lignes alignées 🇦 + 🟩"""
        def letter_to_emoji(c: str) -> str:
            if c.isalpha():
                return chr(0x1F1E6 + (ord(c.upper()) - ord('A')))
            return c.upper()

        letters = " ".join(letter_to_emoji(c) for c in guess)
        colors = []
        for i, c in enumerate(guess):
            if i < len(self.target_word) and c == self.target_word[i]:
                colors.append("🟩")
            elif c in self.target_word:
                colors.append("🟨")
            else:
                colors.append("⬛")
        return f"{letters}\n{' '.join(colors)}"

    def build_embed(self) -> discord.Embed:
        """Construit l'embed affichant l'état du jeu"""
        embed = discord.Embed(
            title="🎯 MOTUS",
            description=f"Mot de **{len(self.target_word)}** lettres",
            color=discord.Color.orange()
        )
        if self.attempts:
            tries_text = "\n\n".join(self.create_feedback_line(guess) for guess in self.attempts)
            embed.add_field(
                name=f"Essais ({len(self.attempts)}/{self.max_attempts})",
                value=tries_text,
                inline=False
            )
        else:
            embed.add_field(
                name="Essais",
                value="*(Aucun essai pour l’instant)*",
                inline=False
            )

        if self.finished:
            if self.attempts[-1] == self.target_word:
                embed.color = discord.Color.green()
                embed.set_footer(text="🎉 Bravo ! Tu as trouvé le mot.")
            else:
                embed.color = discord.Color.red()
                embed.set_footer(text=f"💀 Partie terminée. Le mot était {self.target_word}.")
        return embed

    async def process_guess(self, interaction: discord.Interaction, guess: str):
        """Traite un essai du joueur"""
        if self.finished:
            return  # plus de réponse, la partie est finie

        if len(guess) != len(self.target_word):
            return  # mot invalide, on ignore simplement

        self.attempts.append(guess)

        # Vérifie la victoire ou la fin
        if guess == self.target_word or len(self.attempts) >= self.max_attempts:
            self.finished = True
            for child in self.children:
                child.disabled = True

        # Mettre à jour l'embed
        await safe_edit(self.message, embed=self.build_embed(), view=self)

        # 👇 Correction : répondre au modal silencieusement pour éviter l'erreur
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Bouton principal
# ────────────────────────────────────────────────────────────────────────────────
class MotusButton(Button):
    def __init__(self, parent_view: MotusView):
        super().__init__(label="Proposer un mot", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(MotusModal(self.parent_view))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Motus(commands.Cog):
    """
    Commande /motus et !motus — Lance une partie de Motus
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _start_game(self, channel: discord.abc.Messageable):
        # récupère un mot FR aléatoire entre 5 et 8 lettres
        target_word = await get_random_french_word(length=random.choice(range(5, 9)))
        view = MotusView(target_word)
        embed = view.build_embed()
        view.message = await safe_send(channel, embed=embed, view=view)

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
