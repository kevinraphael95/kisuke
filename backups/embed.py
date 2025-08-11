# ────────────────────────────────────────────────────────────────────────────────
# 📌 sayembed.py — Commande !sayembed
# Objectif : Affiche un message dans un embed, et supprime le message original
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from utils.discord_utils import safe_send  # ✅ Utilisation sécurisée

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class SayEmbed(commands.Cog):
    """
    Commande !embed — Affiche un message dans un embed
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="embed",
        help="Affiche un message dans un embed.",
        description="Le bot supprime le message original et affiche le contenu dans un embed stylisé."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def sayembed(self, ctx: commands.Context, *, message: str):
        """Commande principale pour afficher un message dans un embed."""
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass  # ❌ Ignore silencieusement si la suppression échoue

        embed = discord.Embed(
            description=message,
            color=discord.Color.blurple()
        )
        embed.set_footer(
            text=f"Envoyé par {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )

        try:
            await safe_send(ctx.channel, embed=embed)
        except Exception as e:
            print(f"[ERREUR !embed] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors de l’envoi de l’embed.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SayEmbed(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
