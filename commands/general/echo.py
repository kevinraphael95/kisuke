# ────────────────────────────────────────────────────────────────────────────────
# 📌 echochamber.py — Commande interactive !echochamber
# Objectif : Répéter ton message avec un effet écho rigolo et exagéré
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Modal, InputText
from utils.discord_utils import safe_send, safe_edit, safe_respond  # ✅ Utilisation des safe_

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Modal pour saisir le texte à échochamberiser
# ────────────────────────────────────────────────────────────────────────────────
class EchoModal(Modal):
    def __init__(self):
        super().__init__(title="Echo Chamber")
        self.add_item(InputText(label="Écris ton texte ici", style=discord.InputTextStyle.short, max_length=100))

    async def callback(self, interaction: discord.Interaction):
        texte = self.children[0].value
        echo = echochamber_transform(texte)
        await safe_respond(interaction, f"🔊 **Echochamber** :\n{echo}")

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonction qui transforme le texte en effet écho exagéré
# ────────────────────────────────────────────────────────────────────────────────
def echochamber_transform(text: str) -> str:
    words = text.split()
    echo_parts = []
    for w in words:
        w_low = w.lower()
        # chaque mot est répété 2 ou 3 fois avec effet majuscule exagéré sur dernière répétition
        echo_parts.append(w_low)
        echo_parts.append(w_low[:max(1,len(w)//2)].lower())
        echo_parts.append(w.upper() + "!!!")
    return "… ".join(echo_parts)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class EchoChamberCog(commands.Cog):
    """
    Commande !echochamber — Répète ton texte avec un effet écho exagéré et rigolo
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="echo",
        help="Fais un écho exagéré de ton message.",
        description="Ouvre un formulaire pour saisir un texte, puis te le renvoie en mode écho rigolo."
    )
    async def echochamber(self, ctx: commands.Context):
        """Commande principale qui ouvre un modal pour saisir le texte."""
        try:
            modal = EchoModal()
            await ctx.send_modal(modal)
        except Exception as e:
            print(f"[ERREUR echochamber] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors de l'ouverture du formulaire.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = EchoChamberCog(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
