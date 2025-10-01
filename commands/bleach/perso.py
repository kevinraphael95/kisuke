# ────────────────────────────────────────────────────────────────────────────────
# 📌 perso.py — Commande interactive /perso et !perso
# Objectif : Affiche la fiche d'un personnage Bleach depuis un JSON
# Catégorie : Bleach
# Accès : Tous
# Cooldown : 5s par utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
import json
import os
import random

from utils.discord_utils import safe_send, safe_edit, safe_respond, safe_delete  

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Dossier contenant les JSON des personnages
# ────────────────────────────────────────────────────────────────────────────────
CHAR_DIR = os.path.join("data", "personnages")

def load_character(name: str):
    """Charge la fiche JSON d'un personnage par nom."""
    path = os.path.join(CHAR_DIR, f"{name.lower()}.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_characters():
    """Liste tous les personnages disponibles."""
    files = os.listdir(CHAR_DIR)
    return [f.replace(".json", "") for f in files if f.endswith(".json")]

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Perso(commands.Cog):
    """Commande /perso et !perso — Affiche la fiche d'un personnage."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_character(self, channel: discord.abc.Messageable, name: str = None):
        if not name:
            # Choix aléatoire
            name = random.choice(list_characters())

        char = load_character(name)
        if not char:
            await safe_send(channel, f"❌ Personnage `{name}` introuvable.")
            return

        embed = discord.Embed(
            title=f"{char['nom']}",
            description=f"**Genre:** {char['genre']} | **Sexualité:** {char['sexualite']}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Personnalité", value=", ".join(char["personnalite"]), inline=False)
        embed.add_field(name="Race(s)", value=", ".join(char["race"]), inline=False)
        stats = char["stats_base"]
        embed.add_field(
            name="Stats de base",
            value=(
                f"• Attaque : {stats['attaque']}\n"
                f"• Défense : {stats['defense']}\n"
                f"• Pression : {stats['pression']}\n"
                f"• Kidō : {stats['kido']}\n"
                f"• Intelligence : {stats['intelligence']}\n"
                f"• Rapidité : {stats['rapidite']}\n"
                f"• Total stats : {stats['total_stats']}"
            ),
            inline=False
        )
        for forme_name, forme in char["formes"].items():
            attaque_list = "\n".join(
                f"• {atk['nom']} (Puissance: {atk['puissance']}, Coût: {atk['cout_endurance']})"
                for atk in forme["attaques"]
            )
            embed.add_field(
                name=f"Forme: {forme_name}",
                value=f"Activation: {forme.get('activation','N/A')}\n{attaque_list}",
                inline=False
            )
        if "images" in char:
            embed.set_image(url=char["images"][0])
        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="perso",
        description="Affiche la fiche d'un personnage Bleach"
    )
    @app_commands.describe(name="Nom du personnage (laisser vide pour aléatoire)")
    @app_commands.checks.cooldown(rate=1, per=5.0, key=lambda i: i.user.id)
    async def slash_perso(self, interaction: discord.Interaction, name: str = None):
        await interaction.response.defer()
        await self.send_character(interaction.channel, name)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="perso")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_perso(self, ctx: commands.Context, *, name: str = None):
        await self.send_character(ctx.channel, name)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Perso(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
