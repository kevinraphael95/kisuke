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
import aiohttp
import unicodedata
from spellchecker import SpellChecker
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🌐 Initialisation du spellchecker français
# ────────────────────────────────────────────────────────────────────────────────
spell = SpellChecker(language='fr')

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

    return "PYTHON"

# ────────────────────────────────────────────────────────────────────────────────
# 🌐 Fonction pour vérifier qu’un mot existe via SpellChecker
# ────────────────────────────────────────────────────────────────────────────────
def is_valid_word(word: str) -> bool:
    """Retourne True si le mot est reconnu par SpellChecker"""
    return word.lower() in spell.word_frequency

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
    def __init__(self, target_word: str, max_attempts: int = 6, author_id: int | None = None):
        super().__init__(timeout=180)
        self.target_word = target_word
        self.max_attempts = max_attempts
        self.attempts = []
        self.message = None
        self.finished = False
        self.author_id = author_id  # None si multi
        self.add_item(MotusButton(self))

    # ───────────── Helper pour enlever accents ─────────────
    def remove_accents(self, text: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        ).upper()

    # ───────────── Feedback avec emojis ─────────────
    def create_feedback_line(self, guess: str) -> str:
        """Retourne les deux lignes alignées 🇦 + 🟩"""
        def letter_to_emoji(c: str) -> str:
            c_clean = ''.join(
                ch for ch in unicodedata.normalize('NFD', c)
                if unicodedata.category(ch) != 'Mn'
            ).upper()
            if c_clean.isalpha():
                return chr(0x1F1E6 + (ord(c_clean) - ord('A')))
            return c.upper()

        letters = " ".join(letter_to_emoji(c) for c in guess)
        colors = []
        for i, c in enumerate(guess):
            if i < len(self.target_word) and self.remove_accents(c) == self.remove_accents(self.target_word[i]):
                colors.append("🟩")
            elif self.remove_accents(c) in self.remove_accents(self.target_word):
                colors.append("🟨")
            else:
                colors.append("⬛")
        return f"{letters}\n{' '.join(colors)}"

    # ───────────── Construire l'embed ─────────────
    def build_embed(self) -> discord.Embed:
        """Construit l'embed affichant l'état du jeu"""
        mode_text = "Multi" if self.author_id is None else "Solo"
        embed = discord.Embed(
            title=f"🎯 M🟡TUS - mode {mode_text}",
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
            if self.remove_accents(self.attempts[-1]) == self.remove_accents(self.target_word):
                embed.color = discord.Color.green()
                embed.set_footer(text="🎉 Bravo ! Tu as trouvé le mot.")
            else:
                embed.color = discord.Color.red()
                embed.set_footer(text=f"💀 Partie terminée. Le mot était {self.target_word}.")
        return embed


    # ───────────── Processus d'un essai ─────────────
    async def process_guess(self, interaction: discord.Interaction, guess: str):
        if self.finished:
            return

        if len(guess) != len(self.target_word):
            await safe_respond(interaction, f"⚠️ Le mot doit faire {len(self.target_word)} lettres.", ephemeral=True)
            return

        if not is_valid_word(guess):
            await safe_respond(interaction, f"❌ `{guess}` n’est pas reconnu comme un mot valide.", ephemeral=True)
            return

        self.attempts.append(guess)

        if self.remove_accents(guess) == self.remove_accents(self.target_word) or len(self.attempts) >= self.max_attempts:
            self.finished = True
            for child in self.children:
                child.disabled = True

        await safe_edit(self.message, embed=self.build_embed(), view=self)

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
        if self.parent_view.author_id and interaction.user.id != self.parent_view.author_id:
            await interaction.response.send_message(
                "❌ Seul le lanceur peut proposer un mot.", ephemeral=True
            )
            return
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

    async def _start_game(self, channel: discord.abc.Messageable, author_id: int, mode: str = "solo"):
        target_word = await get_random_french_word(length=random.choice(range(5, 9)))
        # Si mode multi → author_id = None
        author_filter = None if mode.lower() in ("multi", "multijoueur", "m") else author_id
        view = MotusView(target_word, author_id=author_filter)
        embed = view.build_embed()
        view.message = await safe_send(channel, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="motus",
        description="Lance une partie de Motus.  motus multi ou m pour jouer en multi"
    )
    @app_commands.describe(mode="Mode de jeu : solo ou multi")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_motus(self, interaction: discord.Interaction, mode: str = "solo"):
        try:
            await interaction.response.defer()
            await self._start_game(interaction.channel, author_id=interaction.user.id, mode=mode)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /motus] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="motus", 
                      help="Lance une partie de Motus. motus multi ou m pour jouer en multi.")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_motus(self, ctx: commands.Context, mode: str = "solo"):
        try:
            await self._start_game(ctx.channel, author_id=ctx.author.id, mode=mode)
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
