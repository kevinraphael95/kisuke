# ────────────────────────────────────────────────────────────────
#        🧠 COMMANDE DISCORD - FUN FACT BLEACH        
# ────────────────────────────────────────────────────────────────

import discord
import json
import random
from discord.ext import commands

# ────────────────────────────────────────────────────────────────═
# 📦 Classe principale de la commande "funfact"
# ────────────────────────────────────────────────────────────────═
class FunFactCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ───────────────────────────────────────────────
    # 🧠 Commande !funfact : donne un fait intéressant
    # Cooldown : 1 fois toutes les 3 secondes par utilisateur
    # ───────────────────────────────────────────────
    @commands.command(
        name="funfact",
        help="🧠 Donne un fun fact sur Bleach écrit par ChatGPT."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def funfact(self, ctx):
        try:
            # 📂 Lecture du fichier JSON contenant les fun facts
            with open("data/funfacts_bleach.json", "r", encoding="utf-8") as f:
                facts = json.load(f)

            if not facts:
                await ctx.send("❌ Aucun fun fact disponible.")
                return

            # 🎯 Choix aléatoire d’un fait
            fact = random.choice(facts)

            # 📤 Envoi du message avec le fun fact
            await ctx.send(f"🧠 **Fun Fact Bleach :** {fact}")

        # 🚫 Gestion des erreurs
        except FileNotFoundError:
            await ctx.send("❌ Fichier `funfacts_bleach.json` introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : {e}")

    # ✅ Assignation de catégorie automatique
    def cog_load(self):
        self.funfact.category = "Fun"

# ────────────────────────────────────────────────────────────────═
# 🔌 Fonction de setup pour charger le Cog
# ────────────────────────────────────────────────────────────────═
async def setup(bot):
    await bot.add_cog(FunFactCommand(bot))
