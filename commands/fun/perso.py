# ────────────────────────────────────────────────────────────────
#       🧬 COMMANDE DISCORD - PERSONNAGE BLEACH FIXE       
# ────────────────────────────────────────────────────────────────

import discord
import json
from discord.ext import commands

# ────────────────────────────────────────────────────────────────═
# 📦 Classe principale de la commande "perso"
# ────────────────────────────────────────────────────────────────═
class PersoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ───────────────────────────────────────────────
    # 🧬 Commande !perso : quel perso de Bleach es-tu ?
    # Le choix est fixe selon l'utilisateur.
    # ───────────────────────────────────────────────
    @commands.command(
        name="perso",
        help="🧬 Découvre quel personnage de Bleach tu es (choix fixe selon toi)."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown 3s
    async def perso(self, ctx):
        try:
            # 📂 Lecture des personnages
            with open("data/bleach_characters.json", "r", encoding="utf-8") as f:
                characters = json.load(f)

            # ❌ Vérification de validité
            if not characters or not isinstance(characters, list):
                await ctx.send("❌ Le fichier des personnages est vide ou mal formaté.")
                return

            # 🔐 Génération d'un index unique et fixe basé sur l'ID
            user_id = ctx.author.id
            index = (user_id * 31 + 17) % len(characters)
            personnage = characters[index]

            # 📤 Résultat personnalisé
            await ctx.send(
                f"🌌 {ctx.author.mention}, tu es **{personnage}** !\n"
                f"(C'est ta destinée dans le monde de Bleach 🔥)"
            )

        except FileNotFoundError:
            await ctx.send("❌ Fichier `bleach_characters.json` introuvable.")
        except json.JSONDecodeError:
            await ctx.send("❌ Le fichier JSON est mal formaté.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur : {e}")

    # ✅ Catégorie affichée proprement dans le `!help`
    def cog_load(self):
        self.perso.category = "Fun"

# ────────────────────────────────────────────────────────────────═
# 🔌 Fonction de setup pour charger le Cog
# ────────────────────────────────────────────────────────────────═
async def setup(bot):
    cog = PersoCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
