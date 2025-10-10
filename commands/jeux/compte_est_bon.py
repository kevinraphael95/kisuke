# ────────────────────────────────────────────────────────────────────────────────
# 📌 compte_est_bon.py — Jeu interactif /compte_est_bon et !compte_est_bon
# Objectif : Reproduire le jeu "Le Compte est Bon" avec calculs et proposition
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
import random
import asyncio
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
def generate_numbers():
    """Génère 6 nombres (grands et petits) + un objectif."""
    grands = [25, 50, 75, 100]
    petits = [i for i in range(1, 11)] * 2
    selection = random.sample(grands, 2) + random.sample(petits, 4)
    objectif = random.randint(100, 999)
    return selection, objectif

def safe_eval(expr):
    """Évalue un calcul mathématique simple sans danger."""
    allowed_chars = "0123456789+-*/() "
    if any(c not in allowed_chars for c in expr):
        return None
    try:
        result = eval(expr, {"__builtins__": None}, {})
        return round(result)
    except:
        return None

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Interface — Boutons et Formulaire
# ────────────────────────────────────────────────────────────────────────────────
class PropositionModal(Modal):
    def __init__(self, parent, numbers, target):
        super().__init__(title="🧮 Proposer un calcul")
        self.parent = parent
        self.numbers = numbers
        self.target = target
        self.expression = TextInput(
            label="Ton calcul (ex: (100-25)*3)",
            placeholder="Utilise uniquement les nombres affichés et + - * /",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.expression)

    async def on_submit(self, interaction: discord.Interaction):
        expr = self.expression.value.replace(" ", "")
        result = safe_eval(expr)
        if result is None:
            await safe_respond(interaction, "❌ Calcul invalide ou interdit.", ephemeral=True)
            return

        # Vérifie que les nombres utilisés sont valides
        used = [int(n) for n in ''.join(c if c.isdigit() else ' ' for c in expr).split() if n]
        pool = self.numbers.copy()
        for n in used:
            if n in pool:
                pool.remove(n)
            else:
                await safe_respond(interaction, "❌ Tu as utilisé un nombre non disponible.", ephemeral=True)
                return

        diff = abs(self.target - result)
        msg = f"🧠 **{interaction.user.display_name}** → `{expr}` = **{result}** (différence : {diff})"
        if diff == 0:
            msg += "\n🎉 **Le compte est bon !**"
            self.parent.stop_game = True
        await safe_send(interaction.channel, msg)
        await interaction.response.defer()

class CompteBonView(View):
    def __init__(self, numbers, target, is_multi=False):
        super().__init__(timeout=90)
        self.numbers = numbers
        self.target = target
        self.is_multi = is_multi
        self.stop_game = False
        self.add_item(ProposerButton(self))

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True
        if not self.stop_game:
            await safe_send(self.message.channel, "⏱️ Temps écoulé ! Personne n’a trouvé le compte exact.")
        await safe_edit(self.message, view=self)

class ProposerButton(Button):
    def __init__(self, parent):
        super().__init__(label="🧮 Proposer un calcul", style=discord.ButtonStyle.primary)
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        modal = PropositionModal(self.parent, self.parent.numbers, self.parent.target)
        await interaction.response.send_modal(modal)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CompteEstBon(commands.Cog):
    """
    Commande /compte_est_bon et !compte_est_bon — Reproduit le jeu "Le Compte est Bon"
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Lancement du jeu
    # ────────────────────────────────────────────────────────────────────────────
    async def _start_game(self, channel, multi=False):
        numbers, target = generate_numbers()
        embed = discord.Embed(
            title="🧮 Le Compte est Bon",
            description=f"**But :** Atteindre `{target}` avec les nombres suivants :\n"
                        f"`{'  '.join(map(str, numbers))}`\n\n"
                        "Utilise les opérations `+ - * /` pour t’en approcher le plus possible !",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Tu as 90 secondes pour proposer ton calcul.")
        view = CompteBonView(numbers, target, is_multi=multi)
        view.message = await safe_send(channel, embed=embed, view=view)
        await asyncio.sleep(90)
        if not view.stop_game:
            for c in view.children:
                c.disabled = True
            await safe_edit(view.message, view=view)
            await safe_send(channel, "⏱️ Temps écoulé ! Personne n’a trouvé la solution exacte.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="compte_est_bon",
        description="Lance le jeu du Compte est Bon (ajoute 'multi' pour jouer à plusieurs)"
    )
    @app_commands.describe(mode="Écris 'multi' pour activer le mode multijoueur.")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def slash_compte(self, interaction: discord.Interaction, mode: str = None):
        await interaction.response.defer()
        multi = mode and mode.lower() in ["multi", "m"]
        await self._start_game(interaction.channel, multi)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="compte_est_bon", aliases="lceb")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_compte(self, ctx: commands.Context, mode: str = None):
        multi = mode and mode.lower() in ["multi", "m"]
        await self._start_game(ctx.channel, multi)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CompteEstBon(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
