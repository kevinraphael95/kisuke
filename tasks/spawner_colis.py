# ──────────────────────────────────────────────────────────────
# 📁 COLIS - TÂCHE AUTOMATIQUE ET GESTION
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
import random
import asyncio
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from supabase_client import supabase

# 🎁 EFFETS POSSIBLES DANS LES COLIS
EFFETS_COLIS = [
    {"type": "positif", "description": "Tu gagnes 500 points de karma !"},
    {"type": "positif", "description": "Tu obtiens un rôle spécial temporaire !"},
    {"type": "negatif", "description": "Tu es réduit au silence pendant 1h..."},
    {"type": "negatif", "description": "Ton pseudo devient 'Noob officiel' pour 24h."},
    {"type": "neutre", "description": "C'était vide... absolument rien."}
]

# ──────────────────────────────────────────────────────────────
# 🔧 COG : ColisTask
# ──────────────────────────────────────────────────────────────
class ColisTask(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spawn_colis.start()

    def cog_unload(self):
        self.spawn_colis.cancel()

    # 🔁 TÂCHE AUTOMATIQUE : SPAWN COLIS
    @tasks.loop(hours=6)
    async def spawn_colis(self):
        for guild in self.bot.guilds:
            existing = supabase.table("colis") \
                .select("*") \
                .eq("guild_id", str(guild.id)) \
                .eq("ouvert", False) \
                .execute()

            if existing.data:
                continue  # Skip si un colis est déjà actif

            members = [m for m in guild.members if not m.bot and m.status != discord.Status.offline]
            if not members:
                continue

            target = random.choice(members)
            effet = random.choice(EFFETS_COLIS)

            channel = discord.utils.get(guild.text_channels, name="général") or guild.text_channels[0]
            embed = discord.Embed(title="📦 Nouveau colis !", description=f"Un colis mystérieux a été livré à {target.mention}...", color=discord.Color.orange())
            embed.set_footer(text="Clique sur 📦 pour l'ouvrir !")

            msg = await channel.send(content=target.mention, embed=embed)
            await msg.add_reaction("📦")

            supabase.table("colis").insert({
                "guild_id": str(guild.id),
                "user_id": str(target.id),
                "created_at": datetime.utcnow().isoformat(),
                "expire_at": (datetime.utcnow() + timedelta(days=2)).isoformat(),
                "content": effet["description"],
                "channel_id": str(channel.id),
                "message_id": str(msg.id),
                "ouvert": False
            }).execute()

    # 🔁 TÂCHE : Vérifie expiration des colis
    @tasks.loop(hours=1)
    async def check_expired_colis(self):
        now = datetime.utcnow().isoformat()
        data = supabase.table("colis") \
            .select("*") \
            .lte("expire_at", now) \
            .eq("ouvert", False) \
            .execute()

        for colis in data.data:
            guild = self.bot.get_guild(int(colis["guild_id"]))
            if not guild:
                continue

            members = [m for m in guild.members if not m.bot]
            if not members:
                continue

            new_target = random.choice(members)
            supabase.table("colis") \
                .update({"user_id": str(new_target.id), "expire_at": (datetime.utcnow() + timedelta(days=2)).isoformat()}) \
                .eq("id", colis["id"]) \
                .execute()

            channel = guild.get_channel(int(colis["channel_id"]))
            if channel:
                await channel.send(f"📦 Le colis a expiré et a été renvoyé à {new_target.mention} !")

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ColisTask(bot))
    print("✅ Cog chargé : ColisTask (colis auto + expiration)")
