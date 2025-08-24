# ────────────────────────────────────────────────────────────────────────────────
# 📌 jardin.py — Commande interactive /jardin et !jardin
# Objectif : Chaque utilisateur a un jardin persistant avec des fleurs
# Catégorie : Jeu
# Accès : Tout le monde
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import datetime
from utils.discord_utils import safe_send, safe_respond  # ✅
from supabase import create_client, Client

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Connexion Supabase
# ────────────────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "gardens"

# ────────────────────────────────────────────────────────────────────────────────
# 🌱 Constantes du jeu
# ────────────────────────────────────────────────────────────────────────────────
# Configuration jardin par défaut
DEFAULT_GARDEN = {
    "line1": "🌱🌱🌱🌱🌱🌱🌱🌱",
    "line2": "🌱🌱🌱🌱🌱🌱🌱🌱",
    "line3": "🌱🌱🌱🌱🌱🌱🌱🌱",
    "tulipes": 0,
    "roses": 0,
    "jacinthes": 0,
    "hibiscus": 0,
    "paquerettes": 0,
    "tournesols": 0,
    "argent": 0,
    "armee": "",
    "last_fertilize": None,
}

# Dictionnaire fleurs et emojis
FLEUR_EMOJIS = {
    "tulipes": "🌷",
    "roses": "🌹",
    "jacinthes": "🪻",
    "hibiscus": "🌺",
    "paquerettes": "🌼",
    "tournesols": "🌻"
}
FLEUR_LIST = list(FLEUR_EMOJIS.items())  # [(col, emoji), ...]

# Paramètres gameplay
FERTILIZE_COOLDOWN = datetime.timedelta(minutes=10)   # délai entre deux engrais
FERTILIZE_PROBABILITY = 0.05                          # probabilité (5%)


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
async def get_or_create_garden(user_id: int, username: str):
    res = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).execute()
    if res.data:
        return res.data[0]

    new_garden = {"user_id": user_id, "username": username, **DEFAULT_GARDEN}
    supabase.table(TABLE_NAME).insert(new_garden).execute()
    return new_garden

def build_garden_embed(garden: dict, viewer_id: int) -> discord.Embed:
    lines = [garden["line1"], garden["line2"], garden["line3"]]
    inv = " / ".join(f"{FLEUR_EMOJIS[f]}{garden[f]}" for f in FLEUR_EMOJIS)

    # cooldown calcul
    cd_str = "✅ Disponible"
    if garden.get("last_fertilize"):
        last_dt = datetime.datetime.fromisoformat(garden["last_fertilize"])
        remain = last_dt + FERTILIZE_COOLDOWN - datetime.datetime.utcnow()
        if remain.total_seconds() > 0:
            cd_str = f"⏳ {remain.days}j {remain.seconds//3600}h"

    embed = discord.Embed(
        title=f"🏡 Jardin de {garden['username']}",
        description="\n".join(lines),
        color=discord.Color.green()
    )
    embed.add_field(
        name="Infos",
        value=f"Fleurs possédées : {inv}\n"
              f"Armée : {garden['armee'] or '—'} | Argent : {garden['argent']}💰\n"
              f"Cooldown engrais : {cd_str}",
        inline=False
    )
    return embed

def pousser_fleurs(lines: list[str]) -> list[str]:
    new_lines = []
    for line in lines:
        chars = []
        for c in line:
            if c == "🌱" and random.random() < FERTILIZE_PROBABILITY:
                _, emoji = random.choice(FLEUR_LIST)
                chars.append(emoji)
            else:
                chars.append(c)
        new_lines.append("".join(chars))
    return new_lines

def couper_fleurs(lines: list[str], garden: dict) -> tuple[list[str], dict]:
    new_lines = []
    for line in lines:
        chars = []
        for c in line:
            for col, emoji in FLEUR_EMOJIS.items():
                if c == emoji:
                    garden[col] += 1
                    c = "🌱"
            chars.append(c)
        new_lines.append("".join(chars))
    return new_lines, garden

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Boutons d’action
# ────────────────────────────────────────────────────────────────────────────────
class JardinView(discord.ui.View):
    def __init__(self, garden: dict, user_id: int):
        super().__init__(timeout=120)
        self.garden = garden
        self.user_id = user_id

        # désactiver bouton engrais si cooldown
        last = self.garden.get("last_fertilize")
        disabled = False
        if last:
            last_dt = datetime.datetime.fromisoformat(last)
            if datetime.datetime.utcnow() < last_dt + FERTILIZE_COOLDOWN:
                disabled = True
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "Engrais":
                child.disabled = disabled

    @discord.ui.button(label="Engrais", emoji="💩", style=discord.ButtonStyle.green)
    async def engrais(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        # cooldown check
        last = self.garden.get("last_fertilize")
        if last:
            last_dt = datetime.datetime.fromisoformat(last)
            if datetime.datetime.utcnow() < last_dt + FERTILIZE_COOLDOWN:
                return await interaction.response.send_message("⏳ Tu dois attendre avant d'utiliser de l'engrais à nouveau !", ephemeral=True)

        # pousse des fleurs
        lines = [self.garden["line1"], self.garden["line2"], self.garden["line3"]]
        new_lines = pousser_fleurs(lines)

        self.garden["line1"], self.garden["line2"], self.garden["line3"] = new_lines
        self.garden["last_fertilize"] = datetime.datetime.utcnow().isoformat()
        supabase.table(TABLE_NAME).update(self.garden).eq("user_id", self.user_id).execute()

        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=JardinView(self.garden, self.user_id))

    @discord.ui.button(label="Couper", emoji="✂️", style=discord.ButtonStyle.secondary)
    async def couper(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        lines = [self.garden["line1"], self.garden["line2"], self.garden["line3"]]
        new_lines, self.garden = couper_fleurs(lines, self.garden)

        self.garden["line1"], self.garden["line2"], self.garden["line3"] = new_lines
        supabase.table(TABLE_NAME).update(self.garden).eq("user_id", self.user_id).execute()

        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=JardinView(self.garden, self.user_id))

    @discord.ui.button(label="Alchimie", emoji="⚗️", style=discord.ButtonStyle.blurple)
    async def bourse(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚗️ L'alchimie n'est pas encore disponible !", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Jardin(commands.Cog):
    """Commande /jardin et !jardin — Voir son jardin"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="jardin", description="Affiche ton jardin ou celui d'un autre utilisateur 🌱")
    async def slash_jardin(self, interaction: discord.Interaction, user: discord.User = None):
        try:
            target = user or interaction.user
            garden = await get_or_create_garden(target.id, target.name)
            embed = build_garden_embed(garden, interaction.user.id)
            view = None if user else JardinView(garden, interaction.user.id)
            await safe_respond(interaction, embed=embed, view=view)
        except Exception as e:
            print(f"[ERREUR /jardin] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="jardin")
    async def prefix_jardin(self, ctx: commands.Context, user: discord.User = None):
        try:
            target = user or ctx.author
            garden = await get_or_create_garden(target.id, target.name)
            embed = build_garden_embed(garden, ctx.author.id)
            view = None if user else JardinView(garden, ctx.author.id)
            await safe_send(ctx.channel, embed=embed, view=view)
        except Exception as e:
            print(f"[ERREUR !jardin] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Jardin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
