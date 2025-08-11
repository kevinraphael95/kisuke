# ────────────────────────────────────────────────────────────────────────────────
# 📌 say.py — Commande interactive /say et !say
# Objectif : Faire répéter un message par le bot (texte ou embed)
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_delete  # ✅ Utilisation des safe_

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Say(commands.Cog):
    """
    Commande /say et !say — Faire répéter un message par le bot
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _say_message(self, channel: discord.abc.Messageable, message: str, embed: bool = False):
        """Envoie un message (texte ou embed) dans le salon donné."""
        # Nettoyage du message
        message = message.strip()
        if not message:
            return await safe_send(channel, "⚠️ Message vide.")

        # Limite de caractères
        if len(message) > 2000:
            message = message[:1997] + "..."

        # Envoi
        if embed:
            embed_obj = discord.Embed(description=message, color=discord.Color.blurple())
            await safe_send(channel, embed=embed_obj, allowed_mentions=discord.AllowedMentions.none())
        else:
            await safe_send(channel, message, allowed_mentions=discord.AllowedMentions.none())

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="say", description="Le bot répète le message donné.")
    @app_commands.describe(
        message="Message à faire répéter",
        embed="Envoyer le message dans un embed"
    )
    async def slash_say(self, interaction: discord.Interaction, message: str, embed: bool = False):
        """Commande slash principale qui fait répéter un message."""
        try:
            await interaction.response.defer(thinking=False)
            await self._say_message(interaction.channel, message, embed)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /say] {e}")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="say")
    async def prefix_say(self, ctx: commands.Context, *, message: str):
        """
        Commande préfixe qui fait répéter un message.
        Utilise embed en premier argument pour envoyer dans un embed.
        """
        words = message.split(maxsplit=1)
        if words[0].lower() == "embed":
            embed = True
            message = words[1] if len(words) > 1 else ""
        else:
            embed = False

        try:
            await self._say_message(ctx.channel, message, embed)
        finally:
            try:
                await safe_delete(ctx.message)
            except Exception as e:
                print(f"[WARN] safe_delete échoué dans !say : {e}")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Say(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
