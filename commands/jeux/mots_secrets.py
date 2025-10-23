# ────────────────────────────────────────────────────────────────────────────────
# 📌 motssecrets.py — Jeu des Mots Secrets interactif avec Supabase
# Objectif : Trouver des mots pour gagner du Reiatsu
# Catégorie : Jeux / Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands, tasks
from utils.supabase_client import supabase
from utils.discord_utils import safe_send
import json
from pathlib import Path
import asyncio

MOTS_PATH = Path("data/motssecrets.json")
with MOTS_PATH.open("r", encoding="utf-8") as f:
    MOTS = json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class MotsSecretsGame(commands.Cog):
    """
    🎮 Jeu des Mots Secrets — Multijoueur, propose un mot avec !mot <mot>
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_channels = {}  # channel_id: end_time

    # ────────────────────────────────────────────────────────────
    @commands.command(name="motssecrets", aliases=["ms"], help="Lance une session de 3 minutes pour trouver des mots secrets !")
    async def start_session(self, ctx: commands.Context):
        if ctx.channel.id in self.active_channels:
            await safe_send(ctx.channel, "⚠️ Une session est déjà en cours ici !")
            return

        # ── Active la session pour 3 minutes
        self.active_channels[ctx.channel.id] = asyncio.get_event_loop().time() + 180
        await safe_send(ctx.channel, "📝 Session de Mots Secrets lancée ! Tout le monde peut proposer un mot avec `!mot <mot>` pendant 3 minutes !")

        await asyncio.sleep(180)
        self.active_channels.pop(ctx.channel.id, None)
        await safe_send(ctx.channel, "⏰ La session de Mots Secrets est terminée !")

    # ────────────────────────────────────────────────────────────
    @commands.command(name="mot", help="Propose un mot secret pour gagner du Reiatsu")
    async def propose_mot(self, ctx: commands.Context, *, mot: str):
        channel_id = ctx.channel.id
        if channel_id not in self.active_channels:
            await safe_send(ctx.channel, "⚠️ Il n'y a pas de session active ici. Lance une session avec `!motssecrets` !")
            return

        mot_clean = mot.strip().lower()
        mot_data = [m for m in MOTS if m["mot"].lower() == mot_clean]
        if not mot_data:
            await safe_send(ctx.channel, f"❌ `{mot}` n'existe pas dans la liste.")
            return

        mot_id = mot_data[0]["id"]

        # ── Vérifie si l'utilisateur a déjà trouvé ce mot
        found = supabase.table("mots_trouves").select("*").eq("user_id", ctx.author.id).eq("mot_id", mot_id).execute()
        if found.data:
            await safe_send(ctx.channel, f"⚠️ {ctx.author.mention}, tu as déjà trouvé ce mot !")
            return

        # ── Ajoute dans mots_trouves
        supabase.table("mots_trouves").insert({"user_id": ctx.author.id, "mot_id": mot_id}).execute()

        # ── Donne 10 Reiatsu
        user_data = supabase.table("reiatsu").select("points").eq("user_id", ctx.author.id).execute()
        points = user_data.data[0]["points"] if user_data.data else 0
        if user_data.data:
            supabase.table("reiatsu").update({"points": points + 10}).eq("user_id", ctx.author.id).execute()
        else:
            supabase.table("reiatsu").insert({"user_id": ctx.author.id, "points": 10}).execute()

        await safe_send(ctx.channel, f"✅ {ctx.author.mention} a trouvé `{mot_clean}` ! +10 Reiatsu 🎉")

# ────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MotsSecretsGame(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
