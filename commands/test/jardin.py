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
import json
from utils.discord_utils import safe_send, safe_respond
from utils.jardin_utils import (
    get_or_create_garden,
    build_garden_embed,
    pousser_fleurs,
    couper_fleurs,
    AlchimieView,
    JardinView
)
from supabase import create_client, Client

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Connexion Supabase
# ────────────────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ────────────────────────────────────────────────────────────────────────────────
# 🌱 Chargement des constantes depuis JSON
# ────────────────────────────────────────────────────────────────────────────────
with open("data/jardin.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

DEFAULT_GRID = DATA["DEFAULT_GRID"]
DEFAULT_INVENTORY = DATA["DEFAULT_INVENTORY"]
FLEUR_EMOJIS = DATA["FLEUR_EMOJIS"]
FLEUR_LIST = list(FLEUR_EMOJIS.items())
FLEUR_VALUES = DATA["FLEUR_VALUES"]
FLEUR_SIGNS = DATA["FLEUR_SIGNS"]
POTIONS = DATA["POTIONS"]
FERTILIZE_COOLDOWN = DATA["FERTILIZE_COOLDOWN"]
FERTILIZE_PROBABILITY = DATA["FERTILIZE_PROBABILITY"]

TABLE_NAME = DATA.get("TABLE_NAME", "gardens")

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Jardin(commands.Cog):
    """Commande /jardin et !jardin — Voir son jardin"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_garden(self, target_user, viewer_id, respond_func):
        try:
            garden = await get_or_create_garden(target_user.id, target_user.name)
            embed = build_garden_embed(garden, viewer_id)
            view = None
            if target_user.id == viewer_id:
                view = JardinView(garden, viewer_id)
                view.update_buttons()
            await respond_func(embed=embed, view=view)
        except Exception as e:
            print(f"[ERREUR jardin] {e}")
            await respond_func("❌ Une erreur est survenue.", ephemeral=True)

    # ───────── Commande Slash ─────────
    @app_commands.command(name="jardin", description="Affiche ton jardin ou celui d'un autre utilisateur 🌱")
    @app_commands.checks.cooldown(1, 5.0)
    async def slash_jardin(self, interaction: discord.Interaction, user: discord.User = None):
        target = user or interaction.user
        await self._send_garden(target, interaction.user.id, lambda **kwargs: safe_respond(interaction, **kwargs))

    # ───────── Commande Préfixe ─────────
    @commands.command(name="jardin")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def prefix_jardin(self, ctx: commands.Context, user: discord.User = None):
        target = user or ctx.author
        await self._send_garden(target, ctx.author.id, lambda **kwargs: safe_send(ctx.channel, **kwargs))


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Jardin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
