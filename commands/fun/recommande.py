import discord
from discord.ext import commands
import json
import random

class RecommandeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="recommande", help="commande + solo ou multi. Le bot te recommande un jeu avec année et genre.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown utilisateur 3s
    async def recommande(self, ctx, type_jeu: str = None):
        if type_jeu is None:
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
            await ctx.send("❗ Spécifie soit `solo` soit `multi`.")
            return

        jeux = data[type_jeu]
        if not jeux:
            await ctx.send(f"⚠️ Aucun jeu {type_jeu} trouvé.")
            return

        jeu = random.choice(jeux)
        titre = jeu.get("titre", "Jeu inconnu")
        annee = jeu.get("annee", "année inconnue")
        genre = jeu.get("genre", "genre inconnu")

        await ctx.send(
            f"🎮 Jeu **{type_jeu}** recommandé : **{titre}**\n"
            f"🗓️ Année : {annee} | 🧩 Genre : {genre}"
        )

# Chargement auto
async def setup(bot):
    cog = RecommandeCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
