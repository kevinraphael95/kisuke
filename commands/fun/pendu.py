# ────────────────────────────────────────────────────────────────────────────────
# 📌 pendu.py — Commande interactive !pendu
# Objectif : Deviner un mot aléatoire via un jeu du pendu
# Catégorie : Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
from discord.ui import View, Button
import random
import string
import aiohttp

from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🔠 UI — Vue du pendu
# ────────────────────────────────────────────────────────────────────────────────

class PenduView(View):
    def __init__(self, mot, auteur_id):
        super().__init__(timeout=300)
        self.mot = mot.upper()
        self.auteur_id = auteur_id
        self.devine = ["_" if c in string.ascii_uppercase else c for c in self.mot]
        self.erreurs = 0
        self.max_erreurs = 9
        self.lettres_tentees = set()
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        for lettre in string.ascii_uppercase:
            disabled = lettre in self.lettres_tentees
            bouton = Button(label=lettre, style=discord.ButtonStyle.secondary, disabled=disabled)
            bouton.callback = self.make_guess(lettre)
            self.add_item(bouton)

    def make_guess(self, lettre):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.auteur_id:
                await safe_respond(interaction, "Ce n'est pas ton jeu !", ephemeral=True)
                return

            self.lettres_tentees.add(lettre)
            if lettre in self.mot:
                for i, c in enumerate(self.mot):
                    if c == lettre:
                        self.devine[i] = lettre
            else:
                self.erreurs += 1

            if "_" not in self.devine:
                await self.win(interaction)
            elif self.erreurs >= self.max_erreurs:
                await self.lose(interaction)
            else:
                self.update_buttons()
                await self.update_message(interaction)

        return callback

    async def win(self, interaction):
        for item in self.children:
            item.disabled = True
        await safe_edit(self.message, content=f"🎉 Tu as gagné ! Le mot était **{self.mot}**", view=self)

    async def lose(self, interaction):
        for item in self.children:
            item.disabled = True
        await safe_edit(self.message, content=f"💀 Tu as perdu ! Le mot était **{self.mot}**", view=self)

    async def update_message(self, interaction):
        mot_affiche = " ".join(self.devine)
        pendu_txt = f"```\nErreur : {self.erreurs} / {self.max_erreurs}\nMot : {mot_affiche}```"
        await safe_edit(self.message, content=pendu_txt, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Fonction utilitaire : récupérer un mot aléatoire depuis trouve-mot.fr
# ────────────────────────────────────────────────────────────────────────────────

async def get_random_word():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://trouve-mot.fr/api/random") as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("word", "PYTHON")
            else:
                return "PYTHON"  # fallback

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────

class Pendu(commands.Cog):
    """Commande !pendu — Devine un mot aléatoire via un mini-jeu interactif"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="pendu",
        help="Joue au jeu du pendu avec un mot aléatoire.",
        description="Mini-jeu interactif où tu dois deviner un mot aléatoire avant de faire 9 erreurs."
    )
    async def pendu(self, ctx: commands.Context):
        """Lance une partie de pendu avec boutons interractifs."""
        try:
            mot = await get_random_word()
            view = PenduView(mot, ctx.author.id)
            view.message = await safe_send(ctx.channel, f"🕹️ Jeu du pendu\n```Mot : {' '.join(view.devine)}```", view=view)
        except Exception as e:
            print(f"[ERREUR !pendu] {e}")
            await safe_send(ctx.channel, "❌ Erreur lors du lancement du pendu.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────

async def setup(bot: commands.Bot):
    cog = Pendu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
        
