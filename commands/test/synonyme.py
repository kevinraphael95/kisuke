# ────────────────────────────────────────────────────────────────────────────────
# 📌 synonyme.py — Commande /synonyme et !synonyme
# Objectif : Remplacer tous les mots >3 lettres par un synonyme FR aléatoire
# Catégorie : Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
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

class Synonyme(commands.Cog):
    """
    Commande /synonyme et !synonyme — Remplace les mots (>3 lettres) par des synonymes FR
    Source : ConceptNet (Wiktionary/OMW). Pense à créditer la source si ton bot est public.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_synonymes_fr(self, mot: str) -> list[str]:
        """
        Récupère des synonymes FR avec ConceptNet.
        On demande des arêtes /r/Synonym entre /c/fr/<mot> et d'autres /c/fr/*.
        """
        params = (
            f"node=/c/fr/{quote(mot)}"
            f"&rel=/r/Synonym"
            f"&other=/c/fr"
            f"&limit=40"
        )
        url = f"{CONCEPTNET_BASE}?{params}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=6) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
        except Exception:
            return []

        syns = set()
        for edge in data.get("edges", []):
            start = edge.get("start", {}).get("label")
            end = edge.get("end", {}).get("label")
            # On collecte les deux extrémités, on exclut le mot d'origine
            if start and start.lower() != mot.lower():
                syns.add(start)
            if end and end.lower() != mot.lower():
                syns.add(end)

        # On évite de retourner exactement le même mot (variantes de casse)
        return [s for s in syns if s.lower() != mot.lower()]

    async def remplacer_par_synonymes(self, texte: str) -> str:
        """
        Remplace chaque mot >3 lettres par un synonyme aléatoire (FR) si dispo.
        - Respecte la casse initiale
        - Préserve ponctuation, chiffres, emojis, mentions, URLs
        - Pas d'async dans re.sub : on tokenise puis on reconcatène
        """
        # \w inclut lettres/chiffres/_, on filtrera via .isalpha()
        tokens = re.findall(r"\w+|\W+", texte, flags=re.UNICODE)

        cache: dict[str, list[str]] = {}
        pieces: list[str] = []

        for tok in tokens:
            # On remplace uniquement les tokens "mots" alphabétiques
            if tok.isalpha() and len(tok) > 3:
                cle = tok.lower()
                if cle not in cache:
                    cache[cle] = await self.get_synonymes_fr(cle)

                candidats = cache[cle]
                if candidats:
                    choix = random.choice(candidats)
                    # Respect de la majuscule initiale
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
        description="Remplace les mots >3 lettres par des synonymes (FR) aléatoires"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_synonyme(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            message = None

            # On essaie de retrouver un message pertinent (réponse ou dernier message non-bot)
            if interaction.channel:
                if getattr(interaction, "message", None) and interaction.message.reference:
                    message = await interaction.channel.fetch_message(interaction.message.reference.message_id)
                if not message:
                    async for m in interaction.channel.history(limit=15):
                        if not m.author.bot and m.content:
                            message = m
                            break

            if not message:
                await safe_respond(interaction, "❌ Aucun message à modifier trouvé.", ephemeral=True)
                return

            texte_modifie = await self.remplacer_par_synonymes(message.content)
            await safe_respond(
                interaction,
                f"**Original :** {message.content}\n**Modifié :** {texte_modifie}"
            )

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
                async for m in ctx.channel.history(limit=15):
                    if not m.author.bot and m.content:
                        message = m
                        break

            if not message:
                await safe_send(ctx.channel, "❌ Aucun message à modifier trouvé.")
                return

            texte_modifie = await self.remplacer_par_synonymes(message.content)
            await safe_send(ctx.channel, f"**Original :** {message.content}\n**Modifié :** {texte_modifie}")

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
