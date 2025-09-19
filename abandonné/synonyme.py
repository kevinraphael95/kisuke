# ────────────────────────────────────────────────────────────────────────────────
# 📌 synonyme.py — Commande simple /synonyme et !synonyme
# Objectif : Remplacer tous les mots >3 lettres par un synonyme FR aléatoire
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
import asyncio
import random
import re
from urllib.parse import quote

from utils.discord_utils import safe_send, safe_respond

CONCEPTNET_BASE = "https://api.conceptnet.io/query"

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Synonyme(commands.Cog):
    """
    Commande /synonyme et !synonyme — Remplace les mots (>3 lettres) par des synonymes FR
    Source : ConceptNet (Wiktionary/OMW)
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.cache: dict[str, list[str]] = {}

    async def cog_unload(self):
        await self.session.close()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔧 Fonction interne : récupération des synonymes
    # ────────────────────────────────────────────────────────────────────────────
    async def get_synonymes_fr(self, mot: str) -> list[str]:
        """Récupère les synonymes FR via ConceptNet (mise en cache incluse)."""
        mot = mot.lower()
        if mot in self.cache:
            return self.cache[mot]

        params = f"node=/c/fr/{quote(mot)}&rel=/r/Synonym&other=/c/fr&limit=40"
        url = f"{CONCEPTNET_BASE}?{params}"

        try:
            async with self.session.get(url, timeout=6) as resp:
                if resp.status != 200:
                    self.cache[mot] = []
                    return []
                data = await resp.json()
        except asyncio.TimeoutError:
            self.cache[mot] = []
            return []
        except Exception:
            self.cache[mot] = []
            return []

        syns = set()
        for edge in data.get("edges", []):
            start = edge.get("start", {}).get("label")
            end = edge.get("end", {}).get("label")
            if start and start.lower() != mot:
                syns.add(start)
            if end and end.lower() != mot:
                syns.add(end)

        result = [s for s in syns if s.lower() != mot]
        self.cache[mot] = result
        return result

    # ────────────────────────────────────────────────────────────────────────────
    # 🔧 Fonction interne : traitement du texte
    # ────────────────────────────────────────────────────────────────────────────
    async def remplacer_par_synonymes(self, texte: str) -> str:
        """Remplace les mots >3 lettres par un synonyme FR aléatoire si disponible."""
        tokens = re.findall(r"\w+|\W+", texte, flags=re.UNICODE)
        pieces: list[str] = []

        for tok in tokens:
            if tok.isalpha() and len(tok) > 3:
                candidats = await self.get_synonymes_fr(tok)
                if candidats:
                    choix = random.choice(candidats)
                    if tok[0].isupper():
                        choix = choix[:1].upper() + choix[1:]
                    pieces.append(choix)
                else:
                    pieces.append(tok)
            else:
                pieces.append(tok)

        return "".join(pieces)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="synonyme",
        description="Remplace les mots (>3 lettres) par des synonymes FR aléatoires."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_synonyme(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            message = None

            if interaction.channel:
                async for m in interaction.channel.history(limit=15):
                    if not m.author.bot and m.content:
                        message = m
                        break

            if not message:
                await safe_respond(interaction, "❌ Aucun message trouvé à transformer.", ephemeral=True)
                return

            texte_modifie = await self.remplacer_par_synonymes(message.content)
            embed = discord.Embed(title="🔄 Synonymisation", color=discord.Color.blurple())
            embed.add_field(name="💬 Original", value=message.content[:1024], inline=False)
            embed.add_field(name="✨ Modifié", value=texte_modifie[:1024], inline=False)
            await safe_respond(interaction, embed=embed)

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
                async for m in ctx.channel.history(limit=15):
                    if not m.author.bot and m.content:
                        message = m
                        break

            if not message:
                await safe_send(ctx.channel, "❌ Aucun message trouvé à transformer.")
                return

            texte_modifie = await self.remplacer_par_synonymes(message.content)
            embed = discord.Embed(title="🔄 Synonymisation", color=discord.Color.blurple())
            embed.add_field(name="💬 Original", value=message.content[:1024], inline=False)
            embed.add_field(name="✨ Modifié", value=texte_modifie[:1024], inline=False)
            await safe_send(ctx.channel, embed=embed)

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
