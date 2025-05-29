# ────────────────────────────────────────────────────────────────
#        💀 COMMANDE DISCORD - HOLLOWIFICATION        
# ────────────────────────────────────────────────────────────────

import discord
import json
import random
from discord.ext import commands

# ────────────────────────────────────────────────────────────────═
# 📦 Classe principale de la commande "hollowify"
# ────────────────────────────────────────────────────────────────═
class HollowifyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ───────────────────────────────────────────────
    # 💀 Commande !hollowify : transforme un membre
    # Cooldown : 1 fois toutes les 3 secondes par utilisateur
    # ───────────────────────────────────────────────
    @commands.command(
        name="hollowify",
        help="💀 Transforme un utilisateur en Hollow avec une description stylée."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def hollowify(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        try:
            # 📂 Lecture du fichier JSON contenant les données de transformation
            with open("data/hollow_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            prefixes = data.get("prefixes", [])
            suffixes = data.get("suffixes", [])
            descriptions = data.get("descriptions", [])

            # ❌ Vérification des données
            if not prefixes or not suffixes or not descriptions:
                await ctx.send("❌ Le fichier `hollow_data.json` est incomplet ou mal formaté.")
                return

            # 🔀 Génération du nom Hollow et de la description
            nom_hollow = random.choice(prefixes) + random.choice(suffixes)
            description = random.choice(descriptions)

            # 📤 Envoi du message de transformation
            await ctx.send(
                f"💀 **{member.display_name}** se transforme en Hollow : **{nom_hollow}** !\n{description}"
            )

        except FileNotFoundError:
            await ctx.send("❌ Le fichier `hollow_data.json` est introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : {e}")

    # ✅ Assignation propre de la catégorie
    def cog_load(self):
        self.hollowify.category = "Fun"

# ────────────────────────────────────────────────────────────────═
# 🔌 Fonction de setup pour charger le Cog
# ────────────────────────────────────────────────────────────────═
async def setup(bot):
    await bot.add_cog(HollowifyCommand(bot))
