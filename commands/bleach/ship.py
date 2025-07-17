# ────────────────────────────────────────────────────────────────
# 💘 SHIP - COMPATIBILITÉ BLEACH ENTRE DEUX ÂMES
# ────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, button
import json
import hashlib
import random
import asyncio  # nécessaire pour les animations

# Import des fonctions sécurisées pour éviter le rate-limit 429
from discord_utils import safe_send, safe_edit, safe_respond

# ──────────────────────────────────────────────────────────────
# 🧮 FONCTION : Calcul du score de compatibilité
# ──────────────────────────────────────────────────────────────
def calculer_score(p1, p2):
    noms_ordonnes = sorted([p1["nom"], p2["nom"]])
    clef = f"{noms_ordonnes[0]}+{noms_ordonnes[1]}"
    hash_bytes = hashlib.md5(clef.encode()).digest()
    score = int.from_bytes(hash_bytes, 'big') % 101

    if p1.get("genre") != p2.get("genre"):
        score += 5

    races_p1 = set(p1.get("races", []))
    races_p2 = set(p2.get("races", []))
    if not races_p1 & races_p2:
        score -= 10

    stats1 = list(p1["stats"].values())
    stats2 = list(p2["stats"].values())
    avg1 = sum(stats1) / len(stats1)
    avg2 = sum(stats2) / len(stats2)
    diff = abs(avg1 - avg2)

    if diff <= 2:
        score += 5
    elif diff >= 6:
        score -= 10

    return max(0, min(score, 100))

# ──────────────────────────────────────────────────────────────
# 🎛️ VUE INTERACTIVE : Bouton Nouveau Ship
# ──────────────────────────────────────────────────────────────
class ShipView(View):
    def __init__(self, persos, message=None):
        super().__init__(timeout=60)
        self.persos = persos
        self.message = message

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await safe_edit(self.message, view=self)
            except Exception:
                pass

    @button(label="💘 Nouveau ship", style=discord.ButtonStyle.blurple)
    async def nouveau_ship(self, interaction: discord.Interaction, button: discord.ui.Button):
        p1, p2 = random.sample(self.persos, 2)
        score = calculer_score(p1, p2)

        if score >= 90:
            reaction = "âmes sœurs 💞"
            color = discord.Color.magenta()
        elif score >= 70:
            reaction = "une excellente alchimie spirituelle ! 🔥"
            color = discord.Color.red()
        elif score >= 50:
            reaction = "une belle entente possible 🌸"
            color = discord.Color.orange()
        elif score >= 30:
            reaction = "relation instable... mais pas impossible 😬"
            color = discord.Color.yellow()
        else:
            reaction = "aucune chance... ils sont de mondes opposés 💔"
            color = discord.Color.blue()

        embed = discord.Embed(
            title="💘 Test de compatibilité 💘",
            color=color
        )
        embed.add_field(name="👩‍❤️‍👨 Couple", value=f"**{p1['nom']}** ❤️ **{p2['nom']}**", inline=False)
        embed.add_field(name="🔢 Taux d’affinité", value=f"`{score}%`", inline=True)
        embed.add_field(name="💬 Verdict", value=f"*{reaction}*", inline=False)

        if "image" in p1:
            embed.set_thumbnail(url=p1["image"])
        if "image" in p2:
            embed.set_image(url=p2["image"])

        await interaction.response.edit_message(embed=embed, view=self)

# ────────────────────────────────────────────────
# 💞 COMMANDE : !ship
# Tire au sort deux personnages et mesure leur compatibilité
# Basée sur genre, race et statistiques
# ────────────────────────────────────────────────
class ShipCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="ship",
        help="💘 Teste la compatibilité entre deux personnages de Bleach."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def ship(self, ctx):
        try:
            with open("data/bleach_personnages.json", "r", encoding="utf-8") as f:
                persos = json.load(f)

            if len(persos) < 2:
                await safe_send(ctx.channel, "❌ Il faut au moins **deux personnages** pour créer une romance.")
                return

            p1, p2 = random.sample(persos, 2)
            score = calculer_score(p1, p2)

            if score >= 90:
                reaction = "âmes sœurs 💞"
                color = discord.Color.magenta()
            elif score >= 70:
                reaction = "une excellente alchimie spirituelle ! 🔥"
                color = discord.Color.red()
            elif score >= 50:
                reaction = "une belle entente possible 🌸"
                color = discord.Color.orange()
            elif score >= 30:
                reaction = "relation instable... mais pas impossible 😬"
                color = discord.Color.yellow()
            else:
                reaction = "aucune chance... ils sont de mondes opposés 💔"
                color = discord.Color.blue()

            barre = ["⏳", "💞"]
            loading_msg = await safe_send(ctx.channel, "Analyse en cours... " + barre[0])
            for emoji in barre[1:]:
                await asyncio.sleep(1)
                await safe_edit(loading_msg, content=f"Analyse en cours... {emoji}")
            await asyncio.sleep(1.5)

            embed = discord.Embed(
                title="💘 Test de compatibilité 💘",
                color=color
            )
            embed.add_field(name="👩‍❤️‍👨 Couple", value=f"**{p1['nom']}** ❤️ **{p2['nom']}**", inline=False)
            embed.add_field(name="🔢 Taux d’affinité", value=f"`{score}%`", inline=True)
            embed.add_field(name="💬 Verdict", value=f"*{reaction}*", inline=False)

            if "image" in p1:
                embed.set_thumbnail(url=p1["image"])
            if "image" in p2:
                embed.set_image(url=p2["image"])

            view = ShipView(persos)
            message = await safe_edit(loading_msg, content=None, embed=embed, view=view)
            view.message = message  # Permet de gérer le timeout

        except FileNotFoundError:
            await safe_send(ctx.channel, "❌ Le fichier `bleach_personnages.json` est introuvable. Impossible de procéder au *shipping*.")
        except Exception as e:
            await safe_send(ctx.channel, f"⚠️ Une erreur est survenue : `{e}`")

# ────────────────────────────────────────────────
# 🔌 Chargement automatique du cog
# ────────────────────────────────────────────────
async def setup(bot):
    cog = ShipCommand(bot)
    for command in cog.get_commands():
        command.category = "Bleach"
    await bot.add_cog(cog)
