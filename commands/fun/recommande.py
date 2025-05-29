# ────────────────────────────────────────────────────────────────
#       🎮 COMMANDE DISCORD - RECOMMANDATION DE JEUX        
# ────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
import json
import random

# ────────────────────────────────────────────────────────────────═
# 🎲 Classe de la commande "recommande"
# ────────────────────────────────────────────────────────────────═
class RecommandeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────
    # 🎮 Commande !recommande [solo|multi]
    # 🔄 Recommande un jeu avec année & genre
    # ⏱️ Cooldown : 3s par utilisateur
    # ──────────────────────────────────────────────────────
    @commands.command(
        name="recommande",
        help="🎮 commande + `solo` ou `multi`. Recommande un jeu avec année et genre."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def recommande(self, ctx, type_jeu: str = None):
        if not type_jeu:
            await ctx.send("❗ Utilise la commande avec `solo` ou `multi` pour obtenir une recommandation.")
            return

        type_jeu = type_jeu.lower()

        try:
            with open("data/jeux.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            await ctx.send("❌ Le fichier `jeux.json` est introuvable.")
            return
        except json.JSONDecodeError:
            await ctx.send("❌ Le fichier `jeux.json` est mal formé.")
            return

        if type_jeu not in data:
            await ctx.send("❗ Tu dois spécifier soit `solo` soit `multi`.")
            return

        jeux = data[type_jeu]
        if not jeux:
            await ctx.send(f"⚠️ Aucun jeu **{type_jeu}** trouvé.")
            return

        jeu = random.choice(jeux)
        titre = jeu.get("titre", "Jeu inconnu")
        annee = jeu.get("annee", "Année inconnue")
        genre = jeu.get("genre", "Genre inconnu")

        await ctx.send(
            f"🎮 Jeu **{type_jeu}** recommandé : **{titre}**\n"
            f"🗓️ Année : {annee} | 🧩 Genre : {genre}"
        )

    # ✅ Attribution de catégorie
    def cog_load(self):
        self.recommande.category = "Fun"

# ────────────────────────────────────────────────────────────────═
# 🔌 Setup du module
# ────────────────────────────────────────────────────────────────═
async def setup(bot):
    cog = RecommandeCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
