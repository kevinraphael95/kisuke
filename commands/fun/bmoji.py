# ──────────────────────────────────────────────────────────────
# BMOJI
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import json
import random

# ──────────────────────────────────────────────────────────────
# 🎮 COG : BMojiCommand — Jeu d’emoji Bleach
# ──────────────────────────────────────────────────────────────
class BMojiCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # 🔌 Stocke l’instance du bot

    # ──────────────────────────────────────────────────────────
    # 📦 COMMANDE : !bmoji
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="bmoji",
        help="Devine quel personnage Bleach se cache derrière cet emoji."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Anti-spam : 3 secondes
    async def bmoji(self, ctx: commands.Context):
        try:
            # 📖 Lecture du fichier JSON contenant les personnages et emojis
            with open("data/bleach_emojis.json", "r", encoding="utf-8") as f:
                personnages = json.load(f)

            if not personnages:
                await ctx.send("⚠️ Le fichier d'emojis est vide.")
                return

            # 🎯 Choix aléatoire d’un personnage
            personnage = random.choice(personnages)
            nom = personnage.get("nom")  # 🏷️ Nom du perso
            emojis = personnage.get("emojis")  # 😀 Liste d'emojis

            if not nom or not emojis:
                await ctx.send("❌ Erreur de format dans le fichier JSON.")
                return

            # 🎲 Choix aléatoire parmi ses emojis
            emoji_selection = random.choice(emojis)

            # 🔐 Affichage avec spoiler sur le nom du personnage
            await ctx.send(f"{emoji_selection} → ||{nom}||")

        except FileNotFoundError:
            await ctx.send("❌ Fichier `bleach_emojis.json` introuvable dans `data/`.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur inattendue : {e}")

    # 🏷️ Classe la commande dans une catégorie visible par !help
    def cog_load(self):
        self.bmoji.category = "Fun"  # ✅ Catégorie visible dans !commandes / !help

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(BMojiCommand(bot))
    print("✅ Cog chargé : BMojiCommand (catégorie = Fun)")
