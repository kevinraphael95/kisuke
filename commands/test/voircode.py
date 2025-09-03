# ────────────────────────────────────────────────────────────────────────────────
# 📌 view_code_file.py — Commande /view_code_file et !view_code_file
# Objectif : Permet de générer un fichier HTML pour visualiser le code source d'une commande
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

import inspect
import random
import string
from pathlib import Path
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ViewCodeFile(commands.Cog):
    """
    Commande /view_code_file et !view_code_file — Génère un fichier HTML avec le code source d'une commande
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.output_dir = Path("code_view")
        self.output_dir.mkdir(exist_ok=True)

    def generate_html_file(self, code_text: str, command_name: str) -> Path:
        """Crée un fichier HTML coloré avec Pygments et retourne le Path."""
        formatter = HtmlFormatter(full=True, linenos=True, style="friendly", title=f"Code de {command_name}")
        highlighted_code = highlight(code_text, PythonLexer(), formatter)
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        file_path = self.output_dir / f"{command_name}_{token}.html"
        file_path.write_text(highlighted_code, encoding="utf-8")
        return file_path

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="voircode",
        description="Génère un fichier HTML pour visualiser le code source d'une commande"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_view_code_file(self, interaction: discord.Interaction, command_name: str):
        try:
            await interaction.response.defer()
            cmd = self.bot.get_command(command_name)
            if not cmd:
                await safe_respond(interaction, f"❌ Commande `{command_name}` introuvable.", ephemeral=True)
                return
            code = inspect.getsource(cmd.callback)
            file_path = self.generate_html_file(code, command_name)
            await safe_respond(interaction, f"💻 Fichier généré : `{file_path.resolve()}`\nOuvre-le dans ton navigateur !")
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /view_code_file] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="voircode")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_view_code_file(self, ctx: commands.Context, command_name: str):
        try:
            cmd = self.bot.get_command(command_name)
            if not cmd:
                await safe_send(ctx.channel, f"❌ Commande `{command_name}` introuvable.")
                return
            code = inspect.getsource(cmd.callback)
            file_path = self.generate_html_file(code, command_name)
            await safe_send(ctx.channel, f"💻 Fichier généré : `{file_path.resolve()}`\nOuvre-le dans ton navigateur !")
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !view_code_file] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ViewCodeFile(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
