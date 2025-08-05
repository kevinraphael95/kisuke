# ────────────────────────────────────────────────────────────────────────────────
# 📌 pendu.py — Commande interactive !pendu
# Objectif : Mini-jeu de pendu avec mots aléatoires depuis trouve-mot.fr
# Catégorie : Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import aiohttp
import random
import asyncio

from utils.discord_utils import safe_send, safe_edit, safe_respond  # ✅ Utilisation des safe_

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
API_URL = "https://trouve-mot.fr/api/random"

PENDU_STAGES = [
    "`     \n     \n     \n     \n     \n=========`",
    "`     +\n     |\n     |\n     |\n     |\n=========`",
    "` +---+\n     |   |\n         |\n         |\n         |\n=========`",
    "` +---+\n     |   |\n     O   |\n         |\n         |\n=========`",
    "` +---+\n     |   |\n     O   |\n     |   |\n         |\n=========`",
    "` +---+\n     |   |\n     O   |\n    /|\\  |\n         |\n=========`",
    "` +---+\n     |   |\n     O   |\n    /|\\  |\n    / \\  |\n=========`",
]

async def fetch_random_word():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as resp:
            data = await resp.json()
            return data[0]["name"].lower()

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 UI — Vue du pendu avec lettres en boutons
# ────────────────────────────────────────────────────────────────────────────────
class PenduView(View):
    def __init__(self, bot, mot):
        super().__init__(timeout=180)
        self.bot = bot
        self.mot = mot
        self.trouve = set()
        self.rate = set()
        self.max_erreurs = 6
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        for i, lettre in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            style = discord.ButtonStyle.success if lettre.lower() in self.trouve else (
                discord.ButtonStyle.danger if lettre.lower() in self.rate else discord.ButtonStyle.secondary
            )
            self.add_item(PenduButton(self, lettre, style, lettre.lower() in self.trouve | self.rate))

    def get_display_word(self):
        return " ".join([l if l in self.trouve else "_" for l in self.mot])

    def get_pendu_status(self):
        erreurs = len(self.rate)
        pendu_dessin = PENDU_STAGES[erreurs]
        lettres_tentees = ", ".join(sorted(self.trouve | self.rate)).upper() or "Aucune"

        return (
            f"🕹️ **Pendu** — Trouve le mot caché !\n\n"
            f"{pendu_dessin}\n\n"
            f"**Mot :** `{self.get_display_word()}`\n"
            f"**Erreurs :** {erreurs} / {self.max_erreurs}\n"
            f"**Lettres tentées :** {lettres_tentees}"
        )

    async def process_letter(self, interaction: discord.Interaction, lettre: str):
        lettre = lettre.lower()
        if lettre in self.trouve or lettre in self.rate:
            return

        if lettre in self.mot:
            self.trouve.add(lettre)
        else:
            self.rate.add(lettre)

        if all(l in self.trouve for l in set(self.mot)):
            await safe_edit(
                self.message,
                content=f"🎉 **Bravo !** Tu as deviné le mot : `{self.mot}`",
                view=None
            )
            self.stop()
            return

        if len(self.rate) >= self.max_erreurs:
            await safe_edit(
                self.message,
                content=f"💀 **Partie terminée !** Le mot était : `{self.mot}`",
                view=None
            )
            self.stop()
            return

        self.update_buttons()
        await safe_edit(
            self.message,
            content=self.get_pendu_status(),
            view=self
        )

class PenduButton(Button):
    def __init__(self, view: PenduView, lettre: str, style, disabled: bool):
        super().__init__(label=lettre, style=style, disabled=disabled)
        self.lettre = lettre
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        await self.view_ref.process_letter(interaction, self.lettre)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Pendu(commands.Cog):
    """
    Commande !pendu — Mini-jeu du pendu avec lettres en boutons
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="pendu",
        help="Lance une partie de pendu.",
        description="Joue au pendu avec un mot aléatoire."
    )
    async def pendu(self, ctx):
        """Commande principale pour jouer au pendu."""
        try:
            mot = await fetch_random_word()
            view = PenduView(self.bot, mot)
            msg = await safe_send(ctx.channel, view.get_pendu_status(), view=view)
            view.message = msg
        except Exception as e:
            print(f"[ERREUR pendu] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue pendant la partie.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot):
    cog = Pendu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
