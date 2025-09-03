# ────────────────────────────────────────────────────────────────────────────────
# 📌 synonyme.py — Commande /synonyme et !synonyme
# Objectif : Remplacer tous les mots de plus de 3 lettres par un synonyme aléatoire
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
import aiohttp
import random
from utils.discord_utils import safe_send, safe_respond  

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Synonyme(commands.Cog):
    """
    Commande /synonyme et !synonyme — Remplace les mots >3 lettres par des synonymes
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne pour récupérer les synonymes
    # ────────────────────────────────────────────────────────────────────────────
    async def get_synonymes(self, word: str):
        """Récupère des synonymes via l'API Datamuse (max 5)."""
        url = f"https://api.datamuse.com/words?rel_syn={word}&max=5"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return [item['word'] for item in data]
        except Exception:
            pass
        return []

    async def remplacer_par_synonymes(self, texte: str):
        """Remplace tous les mots >3 lettres par un synonyme aléatoire."""
        mots = texte.split()
        texte_modifie = []
        for mot in mots:
            if len(mot) > 3:
                synonymes = await self.get_synonymes(mot)
                if synonymes:
                    mot = random.choice(synonymes)
            texte_modifie.append(mot)
        return ' '.join(texte_modifie)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="synonyme",
        description="Remplace tous les mots >3 lettres par un synonyme aléatoire"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_synonyme(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            # Récupérer le dernier message non-bot ou message répondu
            message = None
            if interaction.message and interaction.message.reference:
                message = await interaction.channel.fetch_message(interaction.message.reference.message_id)
            if not message:
                async for m in interaction.channel.history(limit=10):
                    if not m.author.bot:
                        message = m
                        break
            if not message:
                await safe_respond(interaction, "❌ Aucun message à modifier trouvé.", ephemeral=True)
                return

            texte_modifie = await self.remplacer_par_synonymes(message.content)
            await safe_respond(interaction, f"**Original:** {message.content}\n**Modifié:** {texte_modifie}")

        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /synonyme] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="synonyme")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_synonyme(self, ctx: commands.Context):
        try:
            message = None
            if ctx.message.reference:
                message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if not message:
                async for m in ctx.channel.history(limit=10):
                    if not m.author.bot:
                        message = m
                        break
            if not message:
                await safe_send(ctx.channel, "❌ Aucun message à modifier trouvé.")
                return

            texte_modifie = await self.remplacer_par_synonymes(message.content)
            await safe_send(ctx.channel, f"**Original:** {message.content}\n**Modifié:** {texte_modifie}")

        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !synonyme] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Synonyme(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
