# ────────────────────────────────────────────────────────────────────────────────
# 📌 parti.py — Commande interactive !parti
# Objectif : Générer un nom de parti politique aléatoire
# Catégorie : Fun
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

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "partis_data.json")

def load_data():
    """Charge les données depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class PartiCommand(commands.Cog):
    """
    Commande !parti — Génère un nom de parti politique aléatoire
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="parti",
        help="🏛️ Génère un nom de parti politique aléatoire.",
        description="Génère un nom aléatoire combinant plusieurs morceaux de noms politiques."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def parti(self, ctx: commands.Context):
        """Commande principale qui génère un nom de parti politique."""
        try:
            data = load_data()

            premiers_mots = data.get("premiers_mots", [])
            adjectifs = data.get("adjectifs", [])
            noms = data.get("noms", [])

            if not (premiers_mots and adjectifs and noms):
                await ctx.send("❌ Le fichier `partis_data.json` est incomplet.")
                return

            nom_parti = f"{random.choice(premiers_mots)} {random.choice(adjectifs)} {random.choice(noms)}"

            await ctx.send(f"🏛️ Voici un nom de parti politique : **{nom_parti}**")

        except FileNotFoundError:
            await ctx.send("❌ Fichier `partis_data.json` introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : {e}")

    def cog_load(self):
        self.parti.category = "Fun"

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = PartiCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
