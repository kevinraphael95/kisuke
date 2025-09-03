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
import requests
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
    # 🔹 Fonction interne
    # ────────────────────────────────────────────────────────────────────────────
    def get_synonymes(self, word: str):
        """Récupère des synonymes via l'API Dicolink."""
        try:
            url = f"https://api.dicolink.com/v1/mot/{word}/synonymes?limite=5&api_key=VOTRECLEFAPI"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    return [syn['synonyme'] for syn in data]
        except Exception:
            pass
        return []

    def remplacer_par_synonymes(self, texte: str):
        """Remplace tous les mots >3 lettres par un synonyme aléatoire."""
        mots = texte.split()
        texte_modifie = []
        for mot in mots:
            if len(mot) > 3:
                synonymes = self.get_synonymes(mot)
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
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_synonyme(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            # Récupérer le dernier message non-bot ou message répondu
            msg = interaction.message.reference
            if msg:
                message = await interaction.channel.fetch_message(msg.message_id)
            else:
                async for m in interaction.channel.history(limit=10):
                    if not m.author.bot:
                        message = m
                        break
            texte_modifie = self.remplacer_par_synonymes(message.content)
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
            # Récupérer le dernier message non-bot ou message répondu
            message = ctx.message.reference
            if message:
                msg = await ctx.channel.fetch_message(message.message_id)
            else:
                async for m in ctx.channel.history(limit=10):
                    if not m.author.bot:
                        msg = m
                        break
            texte_modifie = self.remplacer_par_synonymes(msg.content)
            await safe_send(ctx.channel, f"**Original:** {msg.content}\n**Modifié:** {texte_modifie}")
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
            command.category = "Test"
    await bot.add_cog(cog)
