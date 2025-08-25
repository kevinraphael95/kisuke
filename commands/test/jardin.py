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
import json
from utils.discord_utils import safe_send, safe_respond
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
DEFAULT_GRID = [
    "🌱🌱🌱🌱🌱🌱🌱🌱",
    "🌱🌱🌱🌱🌱🌱🌱🌱",
    "🌱🌱🌱🌱🌱🌱🌱🌱",
]
DEFAULT_INVENTORY = {
    "tulipes": 0,
    "roses": 0,
    "jacinthes": 0,
    "hibiscus": 0,
    "paquerettes": 0,
    "tournesols": 0,
}

FLEUR_EMOJIS = {
    "tulipes": "🌷",
    "roses": "🌹",
    "jacinthes": "🪻",
    "hibiscus": "🌺",
    "paquerettes": "🌼",
    "tournesols": "🌻"
}
FLEUR_LIST = list(FLEUR_EMOJIS.items())

FERTILIZE_COOLDOWN = datetime.timedelta(minutes=10)
FERTILIZE_PROBABILITY = 0.39

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
def _jsonify(data):
    return json.loads(json.dumps(data, ensure_ascii=False))

def supabase_json(garden: dict) -> dict:
    return {
        **garden,
        "garden_grid": garden.get("garden_grid", DEFAULT_GRID),
        "inventory": garden.get("inventory", DEFAULT_INVENTORY)
    }

async def get_or_create_garden(user_id: int, username: str) -> dict:
    try:
        res = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).execute()
        if res.data:
            garden = res.data[0]
            garden.setdefault("garden_grid", DEFAULT_GRID)
            garden.setdefault("inventory", DEFAULT_INVENTORY)
            return garden

        new_garden = {
            "user_id": user_id,
            "username": username,
            "garden_grid": DEFAULT_GRID,
            "inventory": DEFAULT_INVENTORY,
            "argent": 0,
            "armee": "",
            "last_fertilize": None
        }
        res = supabase.table(TABLE_NAME).insert(supabase_json(new_garden)).execute()
        if res.error:
            print("[SUPABASE INSERT ERROR]", res.error)
        return new_garden
    except Exception as e:
        print(f"[SUPABASE GET/CREATE ERROR] {e}")
        return {
            "user_id": user_id,
            "username": username,
            "garden_grid": DEFAULT_GRID,
            "inventory": DEFAULT_INVENTORY,
            "argent": 0,
            "armee": "",
            "last_fertilize": None
        }

def build_garden_embed(garden: dict, viewer_id: int) -> discord.Embed:
    lines = garden.get("garden_grid", DEFAULT_GRID)
    inv_dict = garden.get("inventory", DEFAULT_INVENTORY)
    inv = " / ".join(f"{FLEUR_EMOJIS[f]}{inv_dict.get(f,0)}" for f in FLEUR_EMOJIS)

    cd_str = "✅ Disponible"
    last = garden.get("last_fertilize")
    if last:
        try:
            last_dt = datetime.datetime.fromisoformat(last)
            remain = last_dt + FERTILIZE_COOLDOWN - datetime.datetime.utcnow()
            if remain.total_seconds() > 0:
                total_seconds = int(remain.total_seconds())
                minutes, seconds = divmod(total_seconds, 60)
                hours, minutes = divmod(minutes, 60)
                cd_str = f"⏳ {hours}h {minutes}m {seconds}s"
        except Exception:
            cd_str = "✅ Disponible"

    embed = discord.Embed(
        title=f"🏡 Jardin de {garden.get('username', 'Utilisateur')}",
        description="\n".join(lines),
        color=discord.Color.green()
    )
    embed.add_field(
        name="Infos",
        value=f"Fleurs possédées : {inv}\n"
              f"Armée : {garden.get('armee', '—')} | Argent : {garden.get('argent',0)}💰\n"
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
    inv = garden.get("inventory", DEFAULT_INVENTORY)
    for line in lines:
        chars = []
        for c in line:
            for col, emoji in FLEUR_EMOJIS.items():
                if c == emoji:
                    inv[col] = inv.get(col,0)+1
                    c = "🌱"
            chars.append(c)
        new_lines.append("".join(chars))
    garden["inventory"] = inv
    return new_lines, garden

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Boutons d’action corrigés
# ────────────────────────────────────────────────────────────────────────────────
class JardinView(discord.ui.View):
    def __init__(self, garden: dict, user_id: int):
        super().__init__(timeout=120)
        self.garden = garden
        self.user_id = user_id

        # Calcul du cooldown pour Engrais
        last = garden.get("last_fertilize")
        disabled = False
        if last:
            try:
                last_dt = datetime.datetime.fromisoformat(last)
                disabled = datetime.datetime.utcnow() < last_dt + FERTILIZE_COOLDOWN
            except Exception:
                disabled = False

        # Bouton Engrais
        engrais_btn = discord.ui.Button(label="Engrais", emoji="💩", style=discord.ButtonStyle.green, disabled=disabled)
        engrais_btn.callback = self.engrais
        self.add_item(engrais_btn)

        # Bouton Couper
        couper_btn = discord.ui.Button(label="Couper", emoji="✂️", style=discord.ButtonStyle.secondary)
        couper_btn.callback = self.couper
        self.add_item(couper_btn)

        # Bouton Alchimie
        alchimie_btn = discord.ui.Button(label="Alchimie", emoji="⚗️", style=discord.ButtonStyle.blurple)
        alchimie_btn.callback = self.alchimie
        self.add_item(alchimie_btn)

    async def engrais(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        last = self.garden.get("last_fertilize")
        if last:
            try:
                last_dt = datetime.datetime.fromisoformat(last)
                if datetime.datetime.utcnow() < last_dt + FERTILIZE_COOLDOWN:
                    return await interaction.response.send_message(
                        "⏳ Tu dois attendre avant d'utiliser de l'engrais à nouveau !", ephemeral=True
                    )
            except Exception:
                pass

        # Appliquer l'engrais
        self.garden["garden_grid"] = pousser_fleurs(self.garden.get("garden_grid", DEFAULT_GRID))
        self.garden["last_fertilize"] = datetime.datetime.utcnow().isoformat()

        try:
            res = supabase.table(TABLE_NAME).update(supabase_json(self.garden)).eq("user_id", self.user_id).execute()
            if res.error:
                print("[SUPABASE UPDATE ENGRAIS ERROR]", res.error)
        except Exception as e:
            print(f"[SUPABASE UPDATE ENGRAIS EXCEPTION] {e}")

        # Recréer la vue pour désactiver le bouton si nécessaire
        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=JardinView(self.garden, self.user_id))

    async def couper(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        self.garden["garden_grid"], self.garden = couper_fleurs(self.garden.get("garden_grid", DEFAULT_GRID), self.garden)

        try:
            res = supabase.table(TABLE_NAME).update(supabase_json(self.garden)).eq("user_id", self.user_id).execute()
            if res.error:
                print("[SUPABASE UPDATE COUPER ERROR]", res.error)
        except Exception as e:
            print(f"[SUPABASE UPDATE COUPER EXCEPTION] {e}")

        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=JardinView(self.garden, self.user_id))

    async def alchimie(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        embed = discord.Embed(
            title="⚗️ Alchimie",
            description="Fabriquer des potions grâce aux plantes de votre jardin.\n*(Attention : l'alchimie n'est pas encore ajoutée au bot)*",
            color=discord.Color.purple
        )
        await interaction.response.send_message(embed=embed)

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
