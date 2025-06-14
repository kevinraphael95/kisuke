# ────────────────────────────────────────────────────────────────────────────────
# 📌 bmoji.py — Commande interactive !bmoji
# Objectif : Deviner quel personnage Bleach se cache derrière un emoji
# Catégorie : Bleach
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
# 📂 Chargement des données JSON — personnages Bleach avec emojis
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_emojis.json")

def load_characters():
    """Charge la liste des personnages avec leurs emojis depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal — BMojiCommand
# ────────────────────────────────────────────────────────────────────────────────
class BMojiCommand(commands.Cog):
    """
    Commande !bmoji — Devine quel personnage Bleach se cache derrière cet emoji.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="bmoji",
        help="Devine quel personnage Bleach se cache derrière cet emoji."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # Anti-spam 3 secondes
    async def bmoji(self, ctx: commands.Context):
        try:
            personnages = load_characters()
            if not personnages:
                await ctx.send("⚠️ Le fichier d'emojis est vide.")
                return

            personnage = random.choice(personnages)
            nom = personnage.get("nom")
            emojis = personnage.get("emojis")

            if not nom or not emojis:
                await ctx.send("❌ Erreur de format dans le fichier JSON.")
                return

            
            # Extraire tous les emojis individuels dans une liste plate
            all_emojis = []
            for emoji_str in emojis:
                all_emojis.extend(list(emoji_str))

            # Choisir 3 emojis aléatoires (sans doublons)
            if len(all_emojis) < 3:
                await ctx.send("⚠️ Pas assez d'emojis pour ce personnage.")
                return

            emoji_selection = ''.join(random.sample(all_emojis, 3))


            
            embed = discord.Embed(     
                title="🧩 Défi : sauras-tu retrouver à quel personnage de Bleach ces emojis font référence ?",     
                description=f"{emoji_selection} → ||{nom}||",     
                color=discord.Color.orange() ) 
            embed.set_footer(text="Bleach Emoji Challenge") 
            await ctx.send(embed=embed)

        except FileNotFoundError:
            await ctx.send("❌ Fichier `bleach_emojis.json` introuvable dans `data/`.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur inattendue : {e}")




# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = BMojiCommand(bot)
    for command in cog.get_commands():
        command.category = "Bleach"
    await bot.add_cog(cog)
    print("✅ Cog chargé : BMojiCommand (catégorie = Bleach)")

