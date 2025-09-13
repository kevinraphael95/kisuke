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
from discord.ui import View, Modal, TextInput, Button, Select
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
# 🎛️ Vue principale avec boutons (Proposer + Indice)
# ────────────────────────────────────────────────────────────────────────────────
class MotusView(View):
    def __init__(self, target_word: str, max_attempts: int | None = None, author_id: int | None = None):
        # timeout en secondes
        super().__init__(timeout=180)
        self.target_word = target_word.upper()
        # Par défaut : autant d'essais que de lettres
        self.max_attempts = max_attempts if max_attempts is not None else len(self.target_word)
        self.attempts: list[dict] = []  # liste de dicts: {'word': str, 'hint': bool}
        self.message = None  # ← IMPORTANT pour griser les boutons quand on edit
        self.finished = False
        self.author_id = author_id  # None si multi (tout le monde peut jouer)
        self.hinted_indices: set[int] = set()  # indices déjà révélés par indice
        # Ajouter les boutons : indice d'abord, puis proposer
        self.hint_button = HintButton(self)
        self.add_item(self.hint_button)
        self.add_item(MotusButton(self))

    # ───────────── Helper pour enlever accents ─────────────
    def remove_accents(self, text: str) -> str:
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        ).upper()

    # ───────────── Feedback avec emojis ─────────────
    def create_feedback_line(self, entry: dict) -> str:
        """
        Retourne deux lignes :
        - ligne 1 : drapeaux pour lettres révélées ou 🟦 pour non révélées (utilisé pour hints)
        - ligne 2 : couleurs (🟩/🟨/⬛ pour essais normaux), ou 🟦 pour essais 'indice'
        entry = {'word': str, 'hint': bool}
        """
        word = entry['word']
        is_hint = entry.get('hint', False)

        def letter_to_emoji(c: str) -> str:
            c_clean = ''.join(
                ch for ch in unicodedata.normalize('NFD', c)
                if unicodedata.category(ch) != 'Mn'
            ).upper()
            if c_clean.isalpha() and len(c_clean) == 1:
                return chr(0x1F1E6 + (ord(c_clean) - ord('A')))
            # placeholder (ex: '_') -> bleu
            return "🟦"

        # Ligne des "lettres" (drapeaux ou 🟦)
        letters = " ".join(letter_to_emoji(c) for c in word)

        # Ligne des couleurs
        colors = []
        if is_hint:
            # Pour un indice : on n'affiche PAS de vert ; on montre des 🟦 pour indiquer "partiel"
            for i, c in enumerate(word):
                colors.append("🟦")
        else:
            # comportement normal : 🟩 si même position, 🟨 si présent ailleurs, ⬛ sinon
            target = self.target_word
            target_counts = {}
            # compter occurrences pour gestion des jaunes
            for ch in target:
                chn = self.remove_accents(ch)
                target_counts[chn] = target_counts.get(chn, 0) + 1
            # première passe pour verts
            result = [None] * len(word)
            for i, c in enumerate(word):
                if i < len(target) and self.remove_accents(c) == self.remove_accents(target[i]):
                    result[i] = "🟩"
                    target_counts[self.remove_accents(c)] -= 1
            # seconde passe pour jaunes / noirs
            for i, c in enumerate(word):
                if result[i] is not None:
                    continue
                c_clean = self.remove_accents(c)
                if c_clean in target_counts and target_counts[c_clean] > 0:
                    result[i] = "🟨"
                    target_counts[c_clean] -= 1
                else:
                    result[i] = "⬛"
            colors = result

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
            tries_text = "\n\n".join(self.create_feedback_line(entry) for entry in self.attempts)
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
            last_word = self.attempts[-1]['word'] if self.attempts else ""
            if self.remove_accents(last_word) == self.remove_accents(self.target_word):
                embed.color = discord.Color.green()
                embed.set_footer(text="🎉 Bravo ! Tu as trouvé le mot.")
            else:
                embed.color = discord.Color.red()
                embed.set_footer(text=f"💀 Partie terminée. Le mot était {self.target_word}.")
        return embed

    # ───────────── Processus d'un essai ─────────────
    async def process_guess(self, interaction: discord.Interaction, guess: str):
        if self.finished:
            await safe_respond(interaction, "⚠️ La partie est terminée.", ephemeral=True)
            return
        if len(guess) != len(self.target_word):
            await safe_respond(interaction, f"⚠️ Le mot doit faire {len(self.target_word)} lettres.", ephemeral=True)
            return
        if not is_valid_word(guess):
            await safe_respond(interaction, f"❌ `{guess}` n’est pas reconnu comme un mot valide.", ephemeral=True)
            return

        # ajouter l'essai normal
        self.attempts.append({'word': guess.upper(), 'hint': False})

        # victoire ou fin
        if self.remove_accents(guess) == self.remove_accents(self.target_word) or len(self.attempts) >= self.max_attempts:
            self.finished = True
            for child in self.children:
                child.disabled = True

        # Edit du message pour griser boutons / afficher nouvel essai
        try:
            await safe_edit(self.message, embed=self.build_embed(), view=self)
        except Exception as e:
            print(f"[ERREUR edit après essai] {e}")

        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    # ───────────── Timeout (fin de partie sans réponse) ─────────────
    async def on_timeout(self):
        if self.finished:
            return
        self.finished = True
        for child in self.children:
            child.disabled = True
        embed = self.build_embed()
        embed.color = discord.Color.red()
        embed.set_footer(text=f"⏳ Temps écoulé ! Le mot était {self.target_word}.")
        try:
            await safe_edit(self.message, embed=embed, view=self)
        except Exception as e:
            print(f"[ERREUR Timeout Motus] {e}")

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Bouton Indice (utilisable 1x par partie)
# ────────────────────────────────────────────────────────────────────────────────
class HintButton(Button):
    def __init__(self, parent_view: MotusView):
        super().__init__(label="Indice", style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        pv = self.parent_view
        # Permissions : si solo, seul le lanceur peut utiliser
        if pv.author_id and interaction.user.id != pv.author_id:
            await interaction.response.send_message("❌ Seul le lanceur peut utiliser l'indice.", ephemeral=True)
            return
        if pv.finished:
            await interaction.response.send_message("⚠️ La partie est déjà terminée.", ephemeral=True)
            return
        # déterminer positions déjà trouvées (essais normaux qui ont 🟩)
        found_positions = set()
        for entry in pv.attempts:
            if entry.get('hint'):
                continue
            w = entry['word']
            for i, ch in enumerate(w):
                if i < len(pv.target_word) and pv.remove_accents(ch) == pv.remove_accents(pv.target_word[i]):
                    found_positions.add(i)
        # positions déjà hintées
        taken_hint_positions = pv.hinted_indices
        # positions disponibles pour révéler
        available_indices = [i for i in range(len(pv.target_word)) if i not in found_positions and i not in taken_hint_positions]
        if not available_indices:
            await interaction.response.send_message("ℹ️ Aucune lettre restante à dévoiler (toutes déjà trouvées ou révélées).", ephemeral=True)
            return

        # choisir aléatoirement une position à révéler
        idx = random.choice(available_indices)
        letter = pv.target_word[idx]

        # construire mot 'indice' : underscore partout sauf letter à idx
        hint_word = ["_" for _ in range(len(pv.target_word))]
        hint_word[idx] = letter
        hint_str = "".join(hint_word)

        # ajouter l'essai (indice) — coûte un essai
        pv.attempts.append({'word': hint_str, 'hint': True})
        pv.hinted_indices.add(idx)

        # rendre le bouton indisponible (utilisable qu'une seule fois par partie)
        self.disabled = True

        # si ça atteint le max d'essais, finir la partie
        if len(pv.attempts) >= pv.max_attempts:
            pv.finished = True
            for child in pv.children:
                child.disabled = True

        # éditer le message pour afficher l'indice et griser le bouton
        try:
            await safe_edit(pv.message, embed=pv.build_embed(), view=pv)
        except Exception as e:
            print(f"[ERREUR edit après indice] {e}")

        await interaction.response.send_message(f"🔎 Indice utilisé — lettre révélée en position **{idx+1}**.", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Bouton principal (Proposer un mot)
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
        # choisir mot aléatoire (longueur 5-8 par exemple)
        length = random.choice(range(5, 9))
        target_word = await get_random_french_word(length=length)
        # Si mode multi → author_id = None
        author_filter = None if mode.lower() in ("multi", "multijoueur", "m") else author_id
        # max_attempts = nombre de lettres
        view = MotusView(target_word, max_attempts=len(target_word), author_id=author_filter)
        embed = view.build_embed()
        # 🔹 Important pour griser le bouton plus tard
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
    @commands.command(name="motus",                       help="Lance une partie de Motus. motus multi ou m pour jouer en multi.")
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
