# ────────────────────────────────────────────────────────────────────────────────
# 📌 hollowify.py — Commande interactive !hollowify
# Objectif : Transformer un utilisateur en Hollow avec un nom et une description stylée
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
# 📂 Chargement des données JSON (exemple)
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "hollow_data.json")

def load_data():
    """Charge les données depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Pas de menu interactif nécessaire pour cette commande simple
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class HollowifyCommand(commands.Cog):
    """
    Commande !hollowify — Transforme un utilisateur en Hollow avec une description stylée.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="hollowify",
        help="💀 Transforme un utilisateur en Hollow avec une description stylée.",
        description="Attribue un nom Hollow aléatoire et une description stylée à un membre."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def hollowify(self, ctx: commands.Context, member: discord.Member = None):
        """Commande principale !hollowify."""
        member = member or ctx.author
        try:
            data = load_data()
            prefixes = data.get("prefixes", [])
            suffixes = data.get("suffixes", [])
            descriptions = data.get("descriptions", [])

            if not prefixes or not suffixes or not descriptions:
                await ctx.send("❌ Le fichier `hollow_data.json` est incomplet ou mal formaté.")
                return

            nom_hollow = random.choice(prefixes) + random.choice(suffixes)
            description = random.choice(descriptions)

            await ctx.send(
                f"💀 **{member.display_name}** se transforme en Hollow : **{nom_hollow}** !\n{description}"
            )
        except FileNotFoundError:
            await ctx.send("❌ Le fichier `hollow_data.json` est introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : {e}")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HollowifyCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
