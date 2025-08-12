# ────────────────────────────────────────────────────────────────────────────────
# 📌 code.py — Commande !code et /code
# Objectif : Affiche un lien cliquable vers le code source du bot (préfixe + slash)
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
    """Commande !code et /code — Affiche un lien cliquable vers le code source"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.github_url = "https://github.com/kevinraphael95/bleach-discord-bot-test"

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne : Envoi formaté
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_code_link(self, channel: discord.abc.Messageable):
        """Envoie un embed + bouton vers le code source."""
        try:
            # 📌 Création de l'embed
            embed = discord.Embed(
                title="📂 Code source du bot",
                description="Voici le lien vers le dépôt GitHub contenant **tout le code** du bot.",
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png")
            embed.set_footer(text="Bleach Discord Bot — Open Source ❤️")

            # 📌 Bouton cliquable
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="🔗 Voir sur GitHub", url=self.github_url, style=discord.ButtonStyle.link))

            await safe_send(channel, embed=embed, view=view)

        except Exception as e:
            print(f"[ERREUR !code] {e}")
            await safe_send(channel, "❌ Une erreur est survenue lors de l'envoi du lien du code.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="code", help="Affiche un lien vers le code source du bot.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def code(self, ctx: commands.Context):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"[ERREUR suppression message !code] {e}")

        await self._send_code_link(ctx.channel)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="code", description="Affiche un lien vers le code source du bot.")
    async def slash_code(self, interaction: discord.Interaction):
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
