# ────────────────────────────────────────────────────────────────────────────────
# 🧩 anagramme.py — Commande !anagramme
# Objectif : Deviner un mot à partir d’un anagramme
# Catégorie : 🎮 Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import random
import json
import asyncio
from utils.discord_utils import safe_send

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Lecture des données
# ────────────────────────────────────────────────────────────────────────────────
def load_data():
    with open("data/mots.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Vue de jeu (pas de boutons ici, réponse via message)
# ────────────────────────────────────────────────────────────────────────────────
class Anagramme(commands.Cog):
    """
    Commande !anagramme — Devine un mot à partir de ses lettres mélangées.
    """

    def __init__(self, bot):
        self.bot = bot
        self.words = load_data()

    @commands.command(
        name="anagramme",
        help="Devine un mot à partir d’un anagramme.",
        description="Utilisation : !anagramme"
    )
    async def anagramme(self, ctx):
        try:
            mot = random.choice(self.words)
            lettres = list(mot)
            random.shuffle(lettres)
            melange = ''.join(lettres)

            embed = discord.Embed(
                title="🔤 Anagramme !",
                description=f"Devine le mot à partir de ces lettres mélangées :\n**`{melange}`**",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Tu as 30 secondes pour répondre. Réponds dans ce salon.")

            await safe_send(ctx.channel, embed=embed)

            def check(m):
                return m.channel == ctx.channel and m.content.lower() == mot.lower()

            try:
                msg = await self.bot.wait_for("message", check=check, timeout=30.0)
                await safe_send(ctx.channel, f"✅ Bravo {msg.author.mention}, tu as trouvé le mot **{mot}** !")
            except asyncio.TimeoutError:
                await safe_send(ctx.channel, f"⏰ Temps écoulé ! Le mot était : **{mot}**.")

        except Exception as e:
            print(f"[ERREUR anagramme] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors de l’anagramme.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot):
    cog = Anagramme(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
