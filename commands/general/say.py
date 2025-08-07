# ────────────────────────────────────────────────────────────────────────────────
# 📌 say.py — Commande interactive /say et !say
# Objectif : Faire répéter un message par le bot
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

    # 🔹 Commande SLASH
    @app_commands.command(name="say", description="Le bot répète le message donné.")
    @app_commands.describe(message="Message à faire répéter")
    async def slash_say(self, interaction: discord.Interaction, message: str):
        """Commande slash principale qui fait répéter un message."""
        try:
            await interaction.response.defer(thinking=False)  # évite "L’application ne répond plus"
            await safe_send(interaction.channel, message)
            await interaction.delete_original_response()       # supprime toute trace visible
        except Exception as e:
            print(f"[ERREUR /say] {e}")

    # 🔹 Commande PREFIX
    @commands.command(name="say")
    async def prefix_say(self, ctx: commands.Context, *, message: str):
        """Commande préfixe qui fait répéter un message, puis tente de supprimer la commande d'origine."""
        try:
            await safe_send(ctx.channel, message)
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
