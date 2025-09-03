# ────────────────────────────────────────────────────────────────────────────────
# 📌 view_command_file.py — Commande /view_command_file et !view_command_file
# Objectif : Affiche un fichier .py entier depuis le dossier commands dans le navigateur
# Catégorie : Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond  

from pathlib import Path
import random
import string
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ViewCommandFile(commands.Cog):
    """
    Commande /view_command_file et !view_command_file — Génère un fichier HTML avec un fichier .py du dossier commands
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.commands_dir = Path("commands")
        self.output_dir = Path("code_view")
        self.output_dir.mkdir(exist_ok=True)

    def generate_html_file(self, code_text: str, filename: str) -> Path:
        """Crée un fichier HTML coloré avec Pygments et retourne le Path."""
        formatter = HtmlFormatter(full=True, linenos=True, style="friendly", title=filename)
        highlighted_code = highlight(code_text, PythonLexer(), formatter)
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        file_path = self.output_dir / f"{filename}_{token}.html"
        file_path.write_text(highlighted_code, encoding="utf-8")
        return file_path

    def load_command_file(self, filename: str):
        """Charge le contenu d'un fichier .py dans commands."""
        file_path = self.commands_dir / f"{filename}.py"
        if not file_path.exists():
            return None, f"❌ Fichier `{filename}.py` introuvable."
        code = file_path.read_text(encoding="utf-8")
        return code, None

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="voircommande",
        description="Affiche un fichier .py entier depuis commands dans le navigateur"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_view_command_file(self, interaction: discord.Interaction, filename: str):
        try:
            await interaction.response.defer()
            code, error = self.load_command_file(filename)
            if error:
                await safe_respond(interaction, error, ephemeral=True)
                return
            file_path = self.generate_html_file(code, filename)
            await safe_respond(interaction, f"💻 Fichier généré : `{file_path.resolve()}`\nOuvre-le dans ton navigateur !")
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /voircommande] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="voircommande")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_view_command_file(self, ctx: commands.Context, filename: str):
        try:
            code, error = self.load_command_file(filename)
            if error:
                await safe_send(ctx.channel, error)
                return
            file_path = self.generate_html_file(code, filename)
            await safe_send(ctx.channel, f"💻 Fichier généré : `{file_path.resolve()}`\nOuvre-le dans ton navigateur !")
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !voircommande] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ViewCommandFile(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
