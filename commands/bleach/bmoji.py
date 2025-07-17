# ────────────────────────────────────────────────────────────────────────────────
# 📌 bmoji.py — Commande interactive !bmoji
# Objectif : Deviner quel personnage Bleach se cache derrière un emoji
# Catégorie : Bleach
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import json
import random
import os
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON — personnages Bleach avec emojis
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_emojis.json")

def load_characters():
    """Charge la liste des personnages avec leurs emojis depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🛡️ Fonction utilitaire safe_send (anti 429)
# ────────────────────────────────────────────────────────────────────────────────
async def safe_send(ctx_or_interaction, *args, **kwargs):
    """Envoie un message en gérant les erreurs 429 (ratelimit)."""
    tries = 3
    for attempt in range(tries):
        try:
            if hasattr(ctx_or_interaction, "send"):
                return await ctx_or_interaction.send(*args, **kwargs)
            elif hasattr(ctx_or_interaction, "response") and ctx_or_interaction.response.is_done() is False:
                return await ctx_or_interaction.response.send_message(*args, **kwargs)
            else:
                # fallback
                return await ctx_or_interaction.channel.send(*args, **kwargs)
        except discord.errors.HTTPException as e:
            if e.status == 429:
                await asyncio.sleep(2)
            else:
                raise
    # Si on échoue toujours, ignore
    return None

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal — BMojiCommand
# ────────────────────────────────────────────────────────────────────────────────
class BMojiCommand(commands.Cog):
    """
    Commande !bmoji — Devine quel personnage Bleach se cache derrière cet emoji.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="bmoji",
        help="Devine quel personnage Bleach est représenté par ces 3 emojis.",
        description="Affiche 3 emojis aléatoires représentant un personnage de Bleach, tu dois deviner qui c'est !"
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def bmoji(self, ctx: commands.Context):
        try:
            personnages = load_characters()
            if not personnages:
                await safe_send(ctx, "⚠️ Le fichier d'emojis est vide.")
                return

            personnage = random.choice(personnages)
            nom = personnage.get("nom")
            emojis = personnage.get("emojis")

            if not nom or not emojis:
                await safe_send(ctx, "❌ Erreur de format dans le fichier JSON.")
                return

            if len(emojis) < 3:
                await safe_send(ctx, "⚠️ Pas assez d'emojis pour ce personnage.")
                return

            emoji_selection = ''.join(random.sample(emojis, 3))

            embed = discord.Embed(
                title="🧩 Défi : sauras-tu retrouver à quel personnage de Bleach ces emojis font référence ?",
                description=f"{emoji_selection} → ||{nom}||",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Bleach Emoji Challenge")
            await safe_send(ctx, embed=embed)

        except FileNotFoundError:
            await safe_send(ctx, "❌ Fichier `bleach_emojis.json` introuvable dans `data/`.")
        except Exception as e:
            print(f"[ERREUR bmoji] {e}")
            await safe_send(ctx, "⚠️ Une erreur est survenue lors de l'exécution de la commande.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = BMojiCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
