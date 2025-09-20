# ────────────────────────────────────────────────────────────────────────────────
# 📌 mastermind2.py — Commande interactive !mastermind /mastermind
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
        author = None → mode multi (tout le monde)
        author = discord.User → mode solo (seul le lanceur)
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

        # ajouter boutons couleurs + actions
        for color in COLORS:
            self.add_item(MMButton("color", color, self))
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

        # 🔴 bonnes positions
        for i in range(self.code_length):
            if guess[i] == code_copy[i]:
                feedback.append("🔴")
                matched_code[i] = True
                matched_guess[i] = True
            else:
                feedback.append(None)

        # ⚪ bonnes couleurs mauvaises positions
        for i in range(self.code_length):
            if feedback[i] is None:
                for j in range(self.code_length):
                    if not matched_code[j] and not matched_guess[i] and guess[i] == code_copy[j]:
                        feedback[i] = "⚪"
                        matched_code[j] = True
                        matched_guess[i] = True
                        break

        # ❌ couleurs absentes
        for i in range(self.code_length):
            if feedback[i] is None:
                feedback[i] = "❌"

        # corruption aléatoire (mode cauchemar)
        if self.corruption:
            feedback = [f if random.random() > 0.20 else "💀" for f in feedback]

        return feedback

    # ────────────────────────────────────────────────────────────
    async def update_message(self):
        """Met à jour l'embed affiché via safe_edit (sûr vis-à-vis des rate-limits)."""
        if self.message and not self.result_shown:
            try:
                await safe_edit(self.message, embed=self.build_embed(), view=self)
            except Exception:
                # silent fail — on ne veut pas lever d'exception non gérée ici
                pass

    # ────────────────────────────────────────────────────────────
    async def make_attempt(self, interaction: discord.Interaction):
        """Ajoute la tentative, calcule feedback et affiche résultat si besoin."""
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

        # sinon on met à jour l'affichage et on acquitte l'interaction proprement
        await self.update_message()
        try:
            await safe_defer(interaction)
        except Exception:
            pass

    # ────────────────────────────────────────────────────────────
    async def show_result(self, interaction: discord.Interaction, win: bool):
        """Affiche l'écran de résultat et désactive les boutons."""
        self.stop()
        for item in self.children:
            item.disabled = True

        embed = self.build_embed()
        embed.add_field(
            name="🏁 Résultat",
            value=f"**{'Gagné ! 🎉' if win else 'Perdu ! 💀'}**\nLa combinaison était : {' '.join(self.code)}",
            inline=False
        )
        embed.color = discord.Color.green() if win else discord.Color.red()

        # toujours utiliser safe_edit pour l'édition
        try:
            # si on a le message stocké, on l'édite
            if self.message:
                await safe_edit(self.message, embed=embed, view=self)
            else:
                # fallback : éditer le message de l'interaction
                await safe_edit(interaction.message, embed=embed, view=self)
        except Exception:
            # si tout casse, tenter un message ephemeral pour informer
            try:
                await safe_respond(interaction, "✅ Résultat affiché.", ephemeral=True)
            except Exception:
                pass

# ────────────────────────────────────────────────────────────────────────────────
# 🔵 Bouton générique Mastermind (couleurs/actions/difficultés)
# ────────────────────────────────────────────────────────────────
class MMButton(Button):
    def __init__(self, button_type: str, value, view_ref: MastermindView | None = None, author: discord.User | None = None):
        """
        button_type: "color" / "validate" / "clear" / "difficulty"
        value: emoji (pour color) ou label / dict (pour difficulty)
        view_ref: référence MastermindView (pour color/validate/clear)
        author: utilisé pour difficulty (et pour mode solo)
        """
        style = discord.ButtonStyle.secondary
        if button_type == "validate":
            style = discord.ButtonStyle.success
        elif button_type == "clear":
            style = discord.ButtonStyle.danger
        elif button_type == "difficulty":
            style = discord.ButtonStyle.primary

        label = value if button_type == "difficulty" else None
        emoji = None if button_type == "difficulty" else value

        super().__init__(label=label, emoji=emoji, style=style)
        self.button_type = button_type
        self.view_ref = view_ref
        self.author = author
        self.value = value

    async def callback(self, interaction: discord.Interaction):
        """Callback robuste : safe_defer, checks auteur, safe_edit / safe_respond."""
        # acquitter si nécessaire (prévenir InteractionFailed)
        try:
            await safe_defer(interaction)
        except Exception:
            pass

        # mode solo : seul l'auteur peut jouer
        if self.view_ref and self.view_ref.author and interaction.user != self.view_ref.author:
            return await safe_respond(interaction, "⛔ Ce jeu ne t'appartient pas.", ephemeral=True)

        try:
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
                # value est un dict {label, code_length, corruption}
                diff = self.value
                view = MastermindView(self.author, diff["code_length"], diff["corruption"])
                embed = view.build_embed()
                # éditer le message d'origine (on a déjà defer si nécessaire)
                try:
                    # si interaction.message existe, safe_edit dessus
                    await safe_edit(interaction.message, embed=embed, view=view)
                    view.message = interaction.message
                except Exception:
                    # fallback : répondre avec un nouveau message
                    msg = await safe_send(interaction.channel, embed=embed, view=view)
                    view.message = msg

        except Exception as e:
            # log en console + message utilisateur sûr
            print(f"[ERREUR MMButton.callback] {e}")
            try:
                await safe_respond(interaction, "❌ Une erreur est survenue dans le jeu.", ephemeral=True)
            except Exception:
                pass

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
            # ici on stocke le dict entier comme value
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
        # safe_send renvoie le message (géré par utils), on le stocke si besoin
        msg = await safe_send(ctx.channel, embed=embed, view=view)
        try:
            view.message = msg
        except Exception:
            pass

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
        # on répond et on stocke le message lié à l'interaction
        try:
            await interaction.response.send_message(embed=embed, view=view)
            try:
                view.message = await interaction.original_response()
            except Exception:
                view.message = None
        except Exception as e:
            print(f"[ERREUR slash_mastermind send] {e}")
            try:
                await safe_respond(interaction, "❌ Impossible d'ouvrir le jeu.", ephemeral=True)
            except Exception:
                pass

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Mastermind(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
