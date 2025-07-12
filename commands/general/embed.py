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

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class SayEmbed(commands.Cog):
    """Commande !sayembed — Affiche un message dans un embed"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="embed",
        help="Affiche un message dans un embed.",
        description="Le bot supprime le message original et affiche le contenu dans un embed stylisé."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # Anti-spam : 3 sec
    async def sayembed(self, ctx: commands.Context, *, message: str):
        """Commande principale pour afficher un message dans un embed"""
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass  # Ignore silencieusement si la suppression échoue

        embed = discord.Embed(
            description=message,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Envoyé par {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SayEmbed(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
