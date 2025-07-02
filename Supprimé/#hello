# ──────────────────────────────────────────────────────────────
# 📁 HELLO
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import os                      # Gestion des chemins si besoin
import json                    # Lecture de fichiers JSON
import random                  # Choix aléatoire
import discord                 # API Discord
from discord.ext import commands  # Fonctions et outils de commandes

# ──────────────────────────────────────────────────────────────
# ⚙️ CLASSE DU COG : HelloCommand
# ──────────────────────────────────────────────────────────────
class HelloCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """
        Initialise le cog avec le bot en paramètre.
        """
        self.bot = bot

    # ──────────────────────────────────────────────────────────
    # 💬 COMMANDE !hello
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="hello",
        help="Affiche un message de bienvenue aléatoire."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def hello(self, ctx: commands.Context):
        """
        Envoie un message choisi aléatoirement depuis un fichier JSON.
        Si le fichier est manquant ou invalide, un message par défaut est envoyé.
        """
        try:
            # 📁 CHEMIN VERS LE FICHIER DE DONNÉES
            with open("data/hello_messages.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                messages = data.get("messages", [])  # 🔍 Extraction de la clé "messages"

            # 🎲 ENVOI D’UN MESSAGE ALÉATOIRE
            if messages:
                await ctx.send(random.choice(messages))
            else:
                await ctx.send("👋 Hello, je suis en ligne (mais sans message personnalisé) !")

        # 🚨 ERREURS GÉRÉES AVEC PRÉCISION
        except FileNotFoundError:
            await ctx.send("❌ Le fichier `hello_messages.json` est introuvable dans le dossier `data/`.")
        except json.JSONDecodeError:
            await ctx.send("❌ Erreur de syntaxe dans `hello_messages.json` (JSON malformé).")

    # ──────────────────────────────────────────────────────────
    # 🏷️ ATTRIBUTION MANUELLE DE LA CATÉGORIE
    # ──────────────────────────────────────────────────────────
    def cog_load(self):
        """
        Fonction spéciale appelée automatiquement à l’ajout du cog.
        On s’en sert ici pour attribuer dynamiquement une catégorie.
        """
        self.hello.category = "Général"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    """
    Fonction de setup utilisée par Discord.py pour charger ce module.
    Elle ajoute le cog au bot.
    """
    await bot.add_cog(HelloCommand(bot))
    print("✅ Cog chargé : HelloCommand (catégorie = Général)")
