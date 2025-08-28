# ────────────────────────────────────────────────────────────────────────────────
# 📌 redemarrage_command.py — Commande simple /re et !re
# Objectif : Prévenir les membres et redémarrer le bot sur Render (plan gratuit, auto-deploy off)
# Catégorie : ⚙️ Admin
# Accès : Administrateur
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond  # ✅ Anti 429
import os
import sys
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class RedemarrageCommand(commands.Cog):
    """
    Commande /re et !re — Préviens les membres et redémarre le bot.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="re",
        description="(Admin) Préviens les membres et redémarre le bot."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_re(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            await self._restart_bot(interaction.channel)
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /re] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="re",
        help="(Admin) Préviens les membres et redémarre le bot.",
        description="Commande préfixe pour annoncer et relancer le bot."
    )
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def prefix_re(self, ctx: commands.Context):
        await self._restart_bot(ctx.channel)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne de redémarrage
    # ────────────────────────────────────────────────────────────────────────────
    async def _restart_bot(self, channel: discord.abc.Messageable):
        """Annonce le redémarrage et relance le bot."""
        try:
            embed = discord.Embed(
                title="🔃 Redémarrage",
                description="Le bot va redémarrer sous peu...",
                color=discord.Color.red()
            )
            await safe_send(channel, embed=embed)
            await asyncio.sleep(1)  # petit délai pour s'assurer que le message passe
            await self.bot.close()
            os.execv(sys.executable, ["python"] + sys.argv)
        except Exception as e:
            print(f"[RESTART] Erreur lors du redémarrage : {e}")
            await safe_send(channel, f"❌ Impossible de redémarrer le bot : `{e}`")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = RedemarrageCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
