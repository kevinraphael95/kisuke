# ────────────────────────────────────────────────────────────────────────────────
# 📌 generate_requirements.py — Commande simple /generate_requirements et !generate_requirements
# Objectif : Scanner le projet et envoyer un fichier requirements.txt téléchargeable
# Catégorie : Outils
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
# ⚙️ Fonctions internes
# ────────────────────────────────────────────────────────────────────────────────
stdlib = set(stdlib_list.stdlib_list(f"{sys.version_info.major}.{sys.version_info.minor}"))
INTERNAL_DIRS = {"utils", "cogs", "extensions"}
IMPORT_RE = re.compile(r"^(?:from|import)\s+([a-zA-Z0-9_\.]+)")

def is_internal(module: str) -> bool:
    """Vérifie si le module est interne au projet."""
    root = module.split(".")[0]
    return root in INTERNAL_DIRS or root in {"__future__", "__main__"}

def scan_imports(path="."):
    """Parcourt les fichiers .py pour extraire les imports externes."""
    imports = set()
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    for line in f:
                        match = IMPORT_RE.match(line.strip())
                        if match:
                            mod = match.group(1).split(".")[0]
                            if mod not in stdlib and not is_internal(mod):
                                imports.add(mod)
    return sorted(imports)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class GenerateRequirements(commands.Cog):
    """
    Commande /generate_requirements et !generate_requirements — génère un fichier requirements.txt téléchargeable
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _generate(self, channel: discord.abc.Messageable):
        """Scan le projet et envoie un fichier requirements.txt + résumé"""
        external_libs = scan_imports(".")
        if not external_libs:
            await safe_send(channel, "⚠️ Aucune librairie externe détectée.")
            return

        # Création du contenu du fichier en mémoire
        file_content = "\n".join(external_libs) + "\n"
        file = discord.File(io.BytesIO(file_content.encode("utf-8")), filename="requirements.txt")

        # Résumé limité à 10 libs max pour éviter le spam
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
    async def slash_generate(self, interaction: discord.Interaction):
        """Commande slash pour générer requirements.txt"""
        try:
            await interaction.response.defer()
            await self._generate(interaction.channel)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /generate_requirements] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="requirements")
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    async def prefix_generate(self, ctx: commands.Context):
        """Commande préfixe pour générer requirements.txt"""
        try:
            await self._generate(ctx.channel)
        except Exception as e:
            print(f"[ERREUR !generate_requirements] {e}")
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
