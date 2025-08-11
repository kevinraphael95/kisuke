# ────────────────────────────────────────────────────────────────────────────────
# 📌 echo.py — Commande interactive !echo (version sans modal)
# Objectif : Répéter ton message avec un effet écho rigolo et exagéré
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from utils.discord_utils import safe_send

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonction qui transforme le texte en effet écho exagéré
# ────────────────────────────────────────────────────────────────────────────────
def echo_transform(text: str) -> str:
    words = text.split()
    echo_parts = []
    for w in words:
        w_low = w.lower()
        echo_parts.append(w_low)
        echo_parts.append(w_low[:max(1,len(w)//2)])
        echo_parts.append(w.upper() + "!!!")
    return "… ".join(echo_parts)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class EchoCog(commands.Cog):
    """
    Commande !echo — Répète ton texte avec un effet écho exagéré et rigolo
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="echo",
        help="Fais un écho exagéré de ton message.",
        description="Demande un texte puis te le renvoie en mode écho rigolo."
    )
    async def echo(self, ctx: commands.Context):
        """Commande principale qui demande un texte et renvoie l'écho."""
        await safe_send(ctx.channel, "✍️ Écris ton texte à échochamberiser (tu as 60 secondes).")

        def check(m: discord.Message):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60)
        except asyncio.TimeoutError:
            await safe_send(ctx.channel, "⌛ Temps écoulé. Veuillez réessayer la commande.")
            return

        echo = echo_transform(msg.content)
        await safe_send(ctx.channel, f"🔊 **Echo** :\n{echo}")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = EchoCog(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
