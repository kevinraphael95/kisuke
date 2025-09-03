# ────────────────────────────────────────────────────────────────────────────────
# 📌 synonyme.py — Commande /synonyme et !synonyme
# Objectif : Remplacer tous les mots >3 lettres par un synonyme aléatoire
# Catégorie : Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import random
import re
from utils.discord_utils import safe_send, safe_respond  

class Synonyme(commands.Cog):
    """
    Commande /synonyme et !synonyme — Remplace les mots >3 lettres par des synonymes
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
        """Remplace chaque mot >3 lettres par un synonyme aléatoire sans toucher aux autres éléments."""
        async def replace_word(match):
            mot = match.group(0)
            if len(mot) > 3 and mot.isalpha():
                synonymes = await self.get_synonymes(mot.lower())
                if synonymes:
                    mot_syn = random.choice(synonymes)
                    # Respecte la majuscule initiale
                    if mot[0].isupper():
                        mot_syn = mot_syn.capitalize()
                    return mot_syn
            return mot  # ne change rien pour les mots <=3 lettres ou chiffres/ponctuation

        # regex pour capturer les mots uniquement, on laisse les emojis, chiffres, ponctuation intacts
        pattern = r'\b\w+\b'
        texte_modifie = await re.sub(pattern, replace_word, texte)
        return texte_modifie

    @app_commands.command(
        name="synonyme",
        description="Remplace tous les mots >3 lettres par un synonyme aléatoire"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_synonyme(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
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

async def setup(bot: commands.Bot):
    cog = Synonyme(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
