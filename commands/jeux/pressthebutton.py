# ────────────────────────────────────────────────────────────────────────────────
# 📌 pressthebutton.py — Commande interactive /pressthebutton et !pressthebutton
# Objectif : Jeu "Will you press the button?" avec choix Oui/Non
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
from discord.ui import View, Button
import aiohttp
from html import unescape
import random
import string

# Utils sécurisés
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Générateur d'ID unique
# ────────────────────────────────────────────────────────────────────────────────
def get_random_string(length: int = 20) -> str:
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue interactive — boutons Yes/No
# ────────────────────────────────────────────────────────────────────────────────
class PTNView(View):
    def __init__(self, question1: str, question2: str, yes: int, no: int, user: discord.User):
        super().__init__(timeout=60)
        self.question1 = question1
        self.question2 = question2
        self.yes = yes
        self.no = no
        self.user = user

        self.btn_yes = Button(
            style=discord.ButtonStyle.success,
            label="Yes",
            custom_id=get_random_string()
        )
        self.btn_no = Button(
            style=discord.ButtonStyle.danger,
            label="No",
            custom_id=get_random_string()
        )

        self.btn_yes.callback = self.vote_yes
        self.btn_no.callback = self.vote_no

        self.add_item(self.btn_yes)
        self.add_item(self.btn_no)

    async def disable_buttons(self):
        """Désactive les boutons après un vote."""
        for child in self.children:
            child.disabled = True

    async def update_message(self, interaction: discord.Interaction):
        """Met à jour le message avec les résultats et désactive les boutons."""
        self.btn_yes.label = f"Yes ({self.yes})"
        self.btn_no.label = f"No ({self.no})"
        await self.disable_buttons()
        await safe_edit(interaction.message, embed=self.build_embed(), view=self)

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🤔・Will you press the button?",
            description=f"```{self.question1}```\n**But**\n```{self.question2}```",
            color=discord.Color.blurple()
        )
        return embed

    async def vote_yes(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ Ce bouton n'est pas pour toi !", ephemeral=True)
        await interaction.response.defer()
        await self.update_message(interaction)

    async def vote_no(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ Ce bouton n'est pas pour toi !", ephemeral=True)
        await interaction.response.defer()
        await self.update_message(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class PressTheButton(commands.Cog):
    """Commande /pressthebutton et !ptn — Jeu 'Will you press the button?'"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_dilemma(self):
        """Récupère un dilemme depuis l'API publique."""
        url = "https://api2.willyoupressthebutton.com/api/v2/dilemma"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                    if resp.status != 200:
                        print(f"[PTN] Erreur API: statut {resp.status}")
                        return None, None, 0, 0

                    data = await resp.json()
                    if "dilemma" not in data:
                        print(f"[PTN] Réponse inattendue: {data}")
                        return None, None, 0, 0

                    d = data["dilemma"]
                    q1 = unescape(d.get("txt1", "").capitalize())
                    q2 = unescape(d.get("txt2", "").capitalize())
                    yes = d.get("yes", 0)
                    no = d.get("no", 0)
                    return q1, q2, yes, no

        except Exception as e:
            print(f"[PTN] Exception fetch_dilemma: {e}")

        return None, None, 0, 0

    async def _send_game(self, channel: discord.abc.Messageable, user: discord.User):
        """Envoie le dilemme sous forme d'embed avec boutons interactifs."""
        q1, q2, yes, no = await self.fetch_dilemma()
        if not q1 or not q2:
            await safe_send(channel, "❌ Impossible de récupérer un dilemme (API hors service).")
            return

        view = PTNView(q1, q2, yes, no, user)
        await safe_send(channel, embed=view.build_embed(), view=view)

    # ────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="pressthebutton",
        description="Jeu 'Will you press the button?'"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_pressthebutton(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._send_game(interaction.channel, interaction.user)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /pressthebutton] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX (alias !ptn)
    # ────────────────────────────────────────────────────────────────────────
    @commands.command(name="pressthebutton", aliases=["ptn"])
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_pressthebutton(self, ctx: commands.Context):
        try:
            await self._send_game(ctx.channel, ctx.author)
        except Exception as e:
            print(f"[ERREUR !ptn] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = PressTheButton(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
