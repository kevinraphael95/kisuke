# ────────────────────────────────────────────────────────────────────────────────
# 📌 code.py — Commande !code et /code
# Objectif : Affiche le lien vers le code source du bot (préfixe + slash)
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
from utils.discord_utils import safe_send  # ✅ Utilisation sécurisée

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CodeCommand(commands.Cog):
    """
    Commande !code et /code — Affiche le lien du code source du bot
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_code_link(self, channel: discord.abc.Messageable):
        """Envoie le lien vers le code source dans le channel donné."""
        try:
            await safe_send(channel, "🔗 Code source du bot : https://github.com/kevinraphael95/bleach-discord-bot-test")
        except Exception as e:
            print(f"[ERREUR !code] {e}")
            await safe_send(channel, "❌ Une erreur est survenue en envoyant le lien du code.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="code",
        help="Affiche le lien vers le code source du bot sur GitHub.",
        description="Envoie un lien vers le dépôt GitHub contenant le code du bot."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def code(self, ctx: commands.Context):
        """Commande préfixe pour afficher le lien vers le code."""
        try:
            await ctx.message.delete()  # Supprime le message de la commande
        except discord.Forbidden:
            # Pas les permissions, on ignore
            pass
        except Exception as e:
            print(f"[ERREUR suppression message !code] {e}")

        await self._send_code_link(ctx.channel)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="code", description="Affiche le lien vers le code source du bot.")
    async def slash_code(self, interaction: discord.Interaction):
        """Commande slash pour afficher le lien vers le code."""
        await interaction.response.defer(thinking=False)
        await self._send_code_link(interaction.channel)
        await interaction.delete_original_response()

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CodeCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
