# ────────────────────────────────────────────────────────────────────────────────
# 📌 tools_requirements.py — Commande simple /requirements et !requirements
# Objectif : Génère automatiquement un fichier requirements.txt avec les packages installés et l'envoie sur Discord
# Catégorie : Outils_dev
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond
import subprocess
import tempfile

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ToolsRequirements(commands.Cog):
    """
    Commande /requirements et !requirements — Crée un requirements.txt et l'envoie sur Discord
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne pour générer et envoyer requirements.txt
    # ────────────────────────────────────────────────────────────────────────────
    async def _generate_requirements(self, channel: discord.abc.Messageable):
        try:
            # Crée un fichier temporaire pour requirements
            with tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".txt") as tmp_file:
                subprocess.run(["pip", "freeze"], stdout=tmp_file, check=True)
                tmp_file_path = tmp_file.name

            # Envoie le fichier sur Discord
            await channel.send(file=discord.File(tmp_file_path, filename="requirements.txt"))

        except Exception as e:
            print(f"[ERREUR generate_requirements] {e}")
            await safe_send(channel, "❌ Impossible de générer requirements.txt.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="requirements",
        description="Génère et envoie un fichier requirements.txt avec tous les packages installés"
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.user.id))
    async def slash_requirements(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._generate_requirements(interaction.channel)
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /requirements] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="requirements")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_requirements(self, ctx: commands.Context):
        await self._generate_requirements(ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ToolsRequirements(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Outils_dev"
    await bot.add_cog(cog)
