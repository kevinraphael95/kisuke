# ────────────────────────────────────────────────────────────────────────────────
# 📌 perso.py — Commande interactive !perso
# Objectif : Découvre quel personnage de Bleach tu es (choix fixe)
# Catégorie : Bleach
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import json
import os

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON — personnages Bleach
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_characters.json")

def load_characters():
    """Charge la liste des personnages Bleach depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal — PersoCommand
# ────────────────────────────────────────────────────────────────────────────────
class PersoCommand(commands.Cog):
    """
    Commande !perso — Découvre quel personnage de Bleach tu es ou un autre utilisateur.
    Le résultat est fixe selon l'ID Discord.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="perso",
        help="🧬 Découvre quel personnage de Bleach tu es (ou un autre membre).",
        description="Choix déterministe en fonction de l'identifiant Discord."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Anti-spam
    async def perso(self, ctx: commands.Context, membre: discord.Member = None):
        """
        Retourne un personnage de Bleach déterminé par l'utilisateur ou un autre membre mentionné.
        """
        try:
            characters = load_characters()

            if not characters or not isinstance(characters, list):
                await ctx.send("❌ Le fichier des personnages est vide ou mal formaté.")
                return

            cible = membre or ctx.author
            user_id = cible.id
            index = (user_id * 31 + 17) % len(characters)
            personnage = characters[index]

            if cible == ctx.author:
                await ctx.send(
                    f"🌌 {ctx.author.mention}, dans Bleach le personnage qui te ressemble le plus est **{personnage}** ! 🔥"
                )
            else:
                await ctx.send(
                    f"🌌 {ctx.author.mention}, **{cible.display_name}** ressemble à **{personnage}** dans Bleach ! 💫"
                )

        except FileNotFoundError:
            await ctx.send("❌ Fichier `bleach_characters.json` introuvable.")
        except json.JSONDecodeError:
            await ctx.send("❌ Le fichier JSON est mal formaté.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : {e}")

    def cog_load(self):
        self.perso.category = "Bleach"

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = PersoCommand(bot)
    for command in cog.get_commands():
        command.category = "Bleach"
    await bot.add_cog(cog)
    print("✅ Cog chargé : PersoCommand (catégorie = Bleach)")
