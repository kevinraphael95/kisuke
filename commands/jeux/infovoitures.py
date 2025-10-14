# ────────────────────────────────────────────────────────────────────────────────
# 📌 infovoitures.py — Commande /infovoitures et !infovoitures
# Objectif : Afficher la liste des voitures ou la fiche complète d'une voiture
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
import os, json

from utils.discord_utils import safe_send

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON des voitures
# ────────────────────────────────────────────────────────────────────────────────
DATA_PATH = "data/voitures"

def load_voitures():
    voitures = []
    for file in os.listdir(DATA_PATH):
        if file.endswith(".json"):
            with open(os.path.join(DATA_PATH, file), "r", encoding="utf-8") as f:
                voitures.append(json.load(f))
    return voitures

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class InfoVoitures(commands.Cog):
    """
    Commande /infovoitures et !infovoitures — Liste des voitures ou fiche détaillée
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voitures = load_voitures()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction pour afficher toutes les voitures
    # ────────────────────────────────────────────────────────────────────────────
    async def send_liste_voitures(self, channel):
        embed = discord.Embed(
            title="📋 Liste des voitures",
            description="Voici toutes les voitures disponibles :",
            color=discord.Color.blue()
        )
        voitures_sorted = sorted(self.voitures, key=lambda x: x["nom"])
        for v in voitures_sorted:
            embed.add_field(name=v["nom"], value=f"Rareté : {v['rarete']}", inline=True)
        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction pour afficher une voiture spécifique
    # ────────────────────────────────────────────────────────────────────────────
    async def send_voiture_details(self, channel, nom_voiture):
        voiture = next((v for v in self.voitures if v["nom"].lower() == nom_voiture.lower()), None)
        if not voiture:
            return await safe_send(channel, f"❌ Voiture `{nom_voiture}` introuvable.")

        embed = discord.Embed(
            title=f"{voiture['nom']} ({voiture['rarete']})",
            description=voiture.get("description", ""),
            color=discord.Color.green()
        )
        embed.set_image(url=voiture.get("image"))

        stats = voiture.get("stats", {})
        for k, v in stats.items():
            embed.add_field(name=k.replace("_", " ").capitalize(), value=str(v), inline=True)

        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="infovoitures", description="Liste des voitures ou fiche d'une voiture")
    @app_commands.describe(nom="Nom de la voiture (optionnel)")
    async def slash_infovoitures(self, interaction: discord.Interaction, nom: str = None):
        await interaction.response.defer(ephemeral=True)
        if nom:
            await self.send_voiture_details(interaction.channel, nom)
        else:
            await self.send_liste_voitures(interaction.channel)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="infovoitures", aliases=["iv"])
    async def prefix_infovoitures(self, ctx: commands.Context, *, nom: str = None):
        if nom:
            await self.send_voiture_details(ctx.channel, nom)
        else:
            await self.send_liste_voitures(ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = InfoVoitures(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
