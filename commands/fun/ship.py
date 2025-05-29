# ────────────────────────────────────────────────────────────────
# 💘 SHIP - COMPATIBILITÉ BLEACH ENTRE DEUX ÂMES
# ────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import json
import hashlib
import random

class ShipCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ────────────────────────────────────────────────
    # 💞 COMMANDE : !ship
    # Tire au sort deux personnages et mesure leur compatibilité
    # Basée sur genre, race et statistiques
    # ────────────────────────────────────────────────
    @commands.command(
        name="ship",
        help="💘 Fait un couple entre deux personnages de Bleach avec taux de compatibilité."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def ship(self, ctx):
        try:
            with open("data/bleach_personnages.json", "r", encoding="utf-8") as f:
                persos = json.load(f)

            if len(persos) < 2:
                await ctx.send("❌ Il faut au moins **deux personnages** pour créer une romance.")
                return

            # 💫 Sélection aléatoire et déterministe avec hashing
            p1, p2 = random.sample(persos, 2)
            noms_ordonnes = sorted([p1["nom"], p2["nom"]])
            clef = f"{noms_ordonnes[0]}+{noms_ordonnes[1]}"
            hash_bytes = hashlib.md5(clef.encode()).digest()
            score = int.from_bytes(hash_bytes, 'big') % 101

            # 💖 Bonus de diversité de genre
            if p1.get("genre") != p2.get("genre"):
                score += 5

            # ⚔️ Malus d’incompatibilité raciale
            races_p1 = set(p1.get("races", []))
            races_p2 = set(p2.get("races", []))
            if not races_p1 & races_p2:
                score -= 10

            # 📊 Analyse des statistiques de puissance
            stats1 = list(p1["stats"].values())
            stats2 = list(p2["stats"].values())
            avg1 = sum(stats1) / len(stats1)
            avg2 = sum(stats2) / len(stats2)
            diff = abs(avg1 - avg2)

            if diff <= 2:
                score += 5  # 💪 Synergie équilibrée
            elif diff >= 6:
                score -= 10  # 😵 Trop décalés

            # 🧮 Clamp du score final
            score = max(0, min(score, 100))

            # 💌 Réaction finale selon la compatibilité
            if score >= 90:
                reaction = "âmes sœurs destinées à fusionner leurs zanpakutōs 💞"
            elif score >= 70:
                reaction = "une excellente alchimie spirituelle ! 🔥"
            elif score >= 50:
                reaction = "une belle entente possible 🌸"
            elif score >= 30:
                reaction = "relation instable... mais pas impossible 😬"
            else:
                reaction = "aucune chance... ils sont de mondes opposés 💔"

            await ctx.send(
                f"💘 **Compatibilité spirituelle Bleach** 💘\n\n"
                f"👤 {p1['nom']} ❤️ {p2['nom']}\n"
                f"🔢 Taux d’affinité : **{score}%**\n"
                f"💬 Verdict : *{reaction}*"
            )

        except FileNotFoundError:
            await ctx.send("❌ Le fichier `bleach_personnages.json` est introuvable. Impossible de procéder au *shipping*.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : `{e}`")

# ────────────────────────────────────────────────
# 🔌 Chargement automatique du cog
# ────────────────────────────────────────────────
async def setup(bot):
    cog = ShipCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
