# ────────────────────────────────────────────────────────────────────────────────
# 📌 echo.py — Commande interactive !echo
# Objectif : Répéter ton message avec un effet écho rigolo et exagéré
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import Modal, InputText
from utils.discord_utils import safe_send  # safe_respond remplacé car modal doit répondre avec interaction.response

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Modal pour saisir le texte à échochamberiser
# ────────────────────────────────────────────────────────────────────────────────
class EchoModal(Modal):
    def __init__(self):
        super().__init__(title="Echo Chamber")
        self.add_item(InputText(label="Écris ton texte ici", style=discord.InputTextStyle.short, max_length=100))

    async def callback(self, interaction: discord.Interaction):
        texte = self.children[0].value
        echo = echo_transform(texte)
        # Réponse modale correcte obligatoire (interaction.response.send_message)
        await interaction.response.send_message(f"🔊 **echo** :\n{echo}", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonction qui transforme le texte en effet écho exagéré
# ────────────────────────────────────────────────────────────────────────────────
def echo_transform(text: str) -> str:
    words = text.split()
    echo_parts = []
    for w in words:
        w_low = w.lower()
        echo_parts.append(w_low)
        echo_parts.append(w_low[:max(1,len(w)//2)].lower())
        echo_parts.append(w.upper() + "!!!")
    return "… ".join(echo_parts)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class echoCog(commands.Cog):
    """
    Commande !echo — Répète ton texte avec un effet écho exagéré et rigolo
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="echo",
        help="Fais un écho exagéré de ton message.",
        description="Ouvre un formulaire pour saisir un texte, puis te le renvoie en mode écho rigolo."
    )
    async def echo(self, ctx: commands.Context):
        """Commande principale qui ouvre un modal pour saisir le texte."""
        try:
            modal = EchoModal()
            await ctx.send_modal(modal)
        except Exception as e:
            print(f"[ERREUR echo] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors de l'ouverture du formulaire.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = echoCog(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
