# ────────────────────────────────────────────────────────────────────────────────
# 📌 generate_requirements.py — Commande simple /requirements et !requirements
# Objectif : Scanner le projet et générer un fichier requirements.txt téléchargeable
# Catégorie : Outils_dev
# Accès : Tous
# Cooldown : 1 utilisation / 30 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import os
import re
import sys
import io
import stdlib_list
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class GenerateRequirements(commands.Cog):
    """
    Commande /requirements et !requirements — génère un fichier requirements.txt téléchargeable
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _generate_requirements(self, channel: discord.abc.Messageable):
        """Scan le projet et envoie un fichier requirements.txt"""
        # Librairies stdlib pour ignorer
        stdlib = set(stdlib_list.stdlib_list(f"{sys.version_info.major}.{sys.version_info.minor}"))
        internal_dirs = {"utils", "cogs", "extensions"}
        import_re = re.compile(r"^(?:from|import)\s+([a-zA-Z0-9_\.]+)")

        def is_internal(module: str) -> bool:
            return module.split(".")[0] in internal_dirs or module.split(".")[0] in {"__future__", "__main__"}

        imports = set()
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith(".py"):
                    with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                        for line in f:
                            match = import_re.match(line.strip())
                            if match:
                                mod = match.group(1).split(".")[0]
                                if mod not in stdlib and not is_internal(mod):
                                    imports.add(mod)

        external_libs = sorted(imports)
        if not external_libs:
            await safe_send(channel, "⚠️ Aucune librairie externe détectée.")
            return

        file_content = "\n".join(external_libs) + "\n"
        file = discord.File(io.BytesIO(file_content.encode("utf-8")), filename="requirements.txt")

        preview = ", ".join(external_libs[:10])
        if len(external_libs) > 10:
            preview += ", ..."

        await safe_send(
            channel,
            f"✅ Fichier requirements.txt généré avec **{len(external_libs)} librairies** :\n```\n{preview}\n```",
            file=file
        )

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="requirements",
        description="Génère automatiquement un fichier requirements.txt téléchargeable."
    )
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: (i.user.id))
    async def slash_requirements(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._generate_requirements(interaction.channel)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /requirements] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="requirements")
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    async def prefix_requirements(self, ctx: commands.Context):
        try:
            await self._generate_requirements(ctx.channel)
        except Exception as e:
            print(f"[ERREUR !requirements] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = GenerateRequirements(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Outils_dev"
    await bot.add_cog(cog)
