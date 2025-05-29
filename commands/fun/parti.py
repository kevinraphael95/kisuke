# ────────────────────────────────────────────────────────────────
#       🏛️ COMMANDE DISCORD - PARTI POLITIQUE ALÉATOIRE       
# ────────────────────────────────────────────────────────────────

import discord
import json
import random
from discord.ext import commands

# ────────────────────────────────────────────────────────────────═
# 📦 Classe principale de la commande "parti"
# ────────────────────────────────────────────────────────────────═
class PartiCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ───────────────────────────────────────────────
    # 🏛️ Commande !parti : nom de parti aléatoire
    # Cooldown : 1 fois toutes les 3 secondes par utilisateur
    # ───────────────────────────────────────────────
    @commands.command(
        name="parti",
        help="🏛️ Génère un nom de parti politique aléatoire."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def parti(self, ctx):
        try:
            # 📂 Lecture du fichier contenant les morceaux de noms
            with open("data/partis_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            premiers_mots = data.get("premiers_mots", [])
            adjectifs = data.get("adjectifs", [])
            noms = data.get("noms", [])

            # ❌ Vérification des données présentes
            if not (premiers_mots and adjectifs and noms):
                await ctx.send("❌ Le fichier `partis_data.json` est incomplet.")
                return

            # 🧠 Construction aléatoire du nom de parti
            nom_parti = f"{random.choice(premiers_mots)} {random.choice(adjectifs)} {random.choice(noms)}"

            # 📤 Envoi du résultat
            await ctx.send(f"🏛️ Voici un nom de parti politique : **{nom_parti}**")

        except FileNotFoundError:
            await ctx.send("❌ Fichier `partis_data.json` introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : {e}")

    # ✅ Attribution à la catégorie "Fun" pour `!help`
    def cog_load(self):
        self.parti.category = "Fun"

# ────────────────────────────────────────────────────────────────═
# 🔌 Fonction de setup pour charger le Cog
# ────────────────────────────────────────────────────────────────═
async def setup(bot):
    await bot.add_cog(PartiCommand(bot))
