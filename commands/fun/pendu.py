# ────────────────────────────────────────────────────────────────────────────────
# 📌 pendu.py — Commande interactive !pendu
# Objectif : Jeu du pendu avec mot aléatoire depuis l’API trouve-mot.fr
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
# 🔠 Fonction utilitaire — Récupérer un mot depuis l'API
# ────────────────────────────────────────────────────────────────────────────────
async def get_random_word():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://trouve-mot.fr/api/random/1") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data[0]["name"].lower()
    except Exception as e:
        print(f"[ERREUR API pendu] {e}")
    return None

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 UI — Vue du jeu du pendu
# ────────────────────────────────────────────────────────────────────────────────
class PenduView(View):
    def __init__(self, mot_secret):
        super().__init__(timeout=120)
        self.mot_secret = mot_secret
        self.lettres_trouvees = set()
        self.mauvaises_lettres = set()
        self.nb_erreurs = 0
        self.max_erreurs = 6
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True  # tout le monde peut participer

    async def envoyer_etat(self, interaction: discord.Interaction):
        etat_mot = " ".join([l if l in self.lettres_trouvees else "_" for l in self.mot_secret])
        pendu_visuel = [
            "\n😃\n",
            "\n😐\n",
            "\n🙁\n",
            "\n☹️\n",
            "\n😣\n",
            "\n😭\n",
            "\n💀\n"
        ][self.nb_erreurs]

        content = f"```Mot : {etat_mot}\nErreurs : {self.nb_erreurs}/{self.max_erreurs}{pendu_visuel}```"
        if self.message:
            await safe_edit(self.message, content=content, view=self)
        else:
            self.message = await safe_send(interaction.channel, content, view=self)

        if "_" not in etat_mot:
            await safe_edit(self.message, content=f"✅ Bien joué ! Le mot était **{self.mot_secret}**.", view=None)
            self.stop()
        elif self.nb_erreurs >= self.max_erreurs:
            await safe_edit(self.message, content=f"❌ Perdu ! Le mot était **{self.mot_secret}**.", view=None)
            self.stop()

    @discord.ui.button(label="Lettre", style=discord.ButtonStyle.primary, custom_id="pendu_lettre")
    async def demander_lettre(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(LettreModal(self))

# ────────────────────────────────────────────────────────────────────────────────
# ⌨️ Modal — Demander une lettre au joueur
# ────────────────────────────────────────────────────────────────────────────────
class LettreModal(discord.ui.Modal, title="Propose une lettre"):
    lettre = discord.ui.TextInput(label="Lettre", placeholder="Une seule lettre", max_length=1)

    def __init__(self, parent_view: PenduView):
        super().__init__()
        self.parent_view = parent_view

    async def on_submit(self, interaction: discord.Interaction):
        lettre = self.lettre.value.lower()
        if not lettre.isalpha():
            await safe_respond(interaction, "❌ Entre une **lettre valide**.")
            return

        if lettre in self.parent_view.lettres_trouvees or lettre in self.parent_view.mauvaises_lettres:
            await safe_respond(interaction, "⚠️ Lettre déjà proposée.")
            return

        if lettre in self.parent_view.mot_secret:
            self.parent_view.lettres_trouvees.add(lettre)
        else:
            self.parent_view.mauvaises_lettres.add(lettre)
            self.parent_view.nb_erreurs += 1

        await self.parent_view.envoyer_etat(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Pendu(commands.Cog):
    """
    Commande !pendu — Devine un mot lettre par lettre
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="pendu",
        help="Jeu du pendu (devine un mot).",
        description="Jeu du pendu avec un mot aléatoire."
    )
    async def pendu(self, ctx: commands.Context):
        """Commande principale du jeu du pendu."""
        mot = await get_random_word()
        if not mot:
            await safe_send(ctx.channel, "❌ Impossible de récupérer un mot.")
            return

        view = PenduView(mot)
        await view.envoyer_etat(ctx)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Pendu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
