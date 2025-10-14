# ────────────────────────────────────────────────────────────────────────────────
# 📌 infovoitures.py — Commande /infovoitures et !infovoitures
# Objectif : Afficher la liste des voitures ou la fiche complète d'une voiture
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 5 secondes / utilisateur
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
            title="📋 Liste des voitures disponibles",
            color=discord.Color.blurple()
        )

        voitures_sorted = sorted(self.voitures, key=lambda x: x["nom"])
        description_lines = [
            f"**{v['nom']}** — 🏅 {v['rarete'].capitalize()}"
            for v in voitures_sorted
        ]

        embed.description = "\n".join(description_lines)
        embed.set_footer(text=f"{len(voitures_sorted)} voitures disponibles")
        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction pour afficher une voiture spécifique
    # ────────────────────────────────────────────────────────────────────────────
    async def send_voiture_details(self, channel, nom_voiture):
        voiture = next(
            (v for v in self.voitures if v["nom"].lower() == nom_voiture.lower()), 
            None
        )

        if not voiture:
            return await safe_send(channel, f"❌ Voiture `{nom_voiture}` introuvable.")

        # Couleurs selon rareté
        colors = {
            "commun": discord.Color.light_grey(),
            "rare": discord.Color.blue(),
            "épique": discord.Color.purple(),
            "légendaire": discord.Color.gold()
        }
        color = colors.get(voiture["rarete"].lower(), discord.Color.green())

        # Embed compact
        embed = discord.Embed(
            title=f"{voiture['nom']} — {voiture['rarete'].capitalize()}",
            description=voiture.get("description", "Aucune description disponible."),
            color=color
        )

        # ✅ Image affichée correctement
        image_url = voiture.get("image")
        if image_url and image_url.startswith(("http://", "https://")):
            embed.set_thumbnail(url=image_url)  # thumbnail = plus compact
        else:
            embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg")

        # Formatage compact des stats
        stats = voiture.get("stats", {})
        formatted_stats = "\n".join(
            [f"**{k.replace('_', ' ').capitalize()}** : {v}" for k, v in stats.items()]
        )

        embed.add_field(name="📊 Caractéristiques", value=formatted_stats or "Aucune donnée", inline=False)
        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="infovoitures", description="Liste les voitures ou affiche leurs détails")
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
