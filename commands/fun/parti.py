import discord
import json
import random
from discord.ext import commands

class PartiCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="parti",
        help="Génère un nom de parti politique aléatoire."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown 3s
    async def parti(self, ctx):
        try:
            with open("data/partis_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)

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
        self.parti.category = "Fun"  # ✅ Catégorie utilisée par la commande `help`

# Chargement automatique
async def setup(bot):
    await bot.add_cog(PartiCommand(bot))
