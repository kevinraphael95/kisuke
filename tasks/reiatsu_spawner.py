# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu_spawner.py — Gestion du spawn des Reiatsu
# Objectif : Gérer l’apparition et la capture des Reiatsu sur les serveurs
# Catégorie : Reiatsu / RPG
# Accès : Tous
# Cooldown : Spawn auto toutes les X minutes
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
import random
import time
import asyncio
import json
from datetime import datetime
from dateutil import parser
from pathlib import Path
from discord.ext import commands, tasks
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_delete

# ────────────────────────────────────────────────────────────────
# ⚙️ Paramètres globaux
# ────────────────────────────────────────────────────────────────
CONFIG_PATH = Path("data/reiatsu_config.json")
with CONFIG_PATH.open("r", encoding="utf-8") as f:
    CONFIG = json.load(f)

SPAWN_LOOP_INTERVAL = CONFIG["SPAWN_LOOP_INTERVAL"]
SUPER_REIATSU_CHANCE = CONFIG["SUPER_REIATSU_CHANCE"]
SUPER_REIATSU_GAIN = CONFIG["SUPER_REIATSU_GAIN"]
NORMAL_REIATSU_GAIN = CONFIG["NORMAL_REIATSU_GAIN"]
SPAWN_SPEED_RANGES = CONFIG["SPAWN_SPEED_RANGES"]
DEFAULT_SPAWN_SPEED = CONFIG["DEFAULT_SPAWN_SPEED"]
CLASSES = CONFIG["CLASSES"]

# ────────────────────────────────────────────────────────────────
# 🧠 Cog : ReiatsuSpawner
# ────────────────────────────────────────────────────────────────
class ReiatsuSpawner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.locks = {}

    async def cog_load(self):
        asyncio.create_task(self._check_on_startup())
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    # ──────────────────────────────────────────────────────────────
    async def _check_on_startup(self):
        await self.bot.wait_until_ready()
        configs = supabase.table("reiatsu_config").select("*").execute()
        for conf in configs.data:
            if not conf.get("is_spawn") or not conf.get("message_id"):
                continue
            guild = self.bot.get_guild(int(conf["guild_id"]))
            if not guild:
                continue
            channel = guild.get_channel(int(conf.get("channel_id") or 0))
            if not channel:
                continue
            try:
                await channel.fetch_message(int(conf["message_id"]))
            except Exception:
                supabase.table("reiatsu_config").update({
                    "is_spawn": False,
                    "message_id": None
                }).eq("guild_id", int(conf["guild_id"])).execute()
                print(f"[RESET] Reiatsu fantôme nettoyé pour guild {conf['guild_id']}")

    # ───────────────────────────────────────────────────────────────
    @tasks.loop(seconds=SPAWN_LOOP_INTERVAL)
    async def spawn_loop(self):
        await self.bot.wait_until_ready()
        if not getattr(self.bot, "is_main_instance", True):
            return
        try:
            await self._spawn_tick()
        except Exception as e:
            print(f"[ERREUR spawn_loop] {e}")

    async def _spawn_tick(self):
        now = int(time.time())
        configs = supabase.table("reiatsu_config").select("*").execute()
        for conf in configs.data:
            guild_id = int(conf["guild_id"])
            channel_id = conf.get("channel_id")
            if not channel_id:
                continue
            last_spawn_str = conf.get("last_spawn_at")
            spawn_speed = conf.get("spawn_speed") or DEFAULT_SPAWN_SPEED
            min_delay, max_delay = SPAWN_SPEED_RANGES.get(spawn_speed, SPAWN_SPEED_RANGES[DEFAULT_SPAWN_SPEED])
            delay = conf.get("spawn_delay") or random.randint(min_delay, max_delay)
            should_spawn = not last_spawn_str or (now - int(parser.parse(last_spawn_str).timestamp()) >= delay)
            channel = self.bot.get_channel(int(channel_id))
            if should_spawn and not conf.get("is_spawn", False) and channel:
                await self._spawn_message(channel, guild_id)

            # Spawn faux Reiatsu Illusionniste
            if channel:
                await self._spawn_faux_reiatsu(channel)

    # ───────────────────────────────────────────────────────────────
    async def _spawn_message(self, channel, guild_id: int, is_fake=False, owner_id=None):
        title = "💠 Un Reiatsu sauvage apparaît !"
        desc = "Cliquez sur la réaction 💠 pour l'absorber."
        color = discord.Color.purple()
        embed = discord.Embed(title=title, description=desc, color=color)
        message = await safe_send(channel, embed=embed)
        if not message:
            return
        try:
            await message.add_reaction("💠")
        except discord.HTTPException:
            pass

        if is_fake:
            supabase.table("reiatsu").update({
                "fake_spawn_id": str(message.id),
                "fake_spawn_guild_id": str(channel.guild.id)
            }).eq("user_id", owner_id).execute()
            asyncio.create_task(self._delete_fake_after_timeout(channel, message.id, owner_id))
        else:
            supabase.table("reiatsu_config").update({
                "is_spawn": True,
                "last_spawn_at": datetime.utcnow().isoformat(timespec="seconds"),
                "message_id": str(message.id)
            }).eq("guild_id", guild_id).execute()

    async def _delete_fake_after_timeout(self, channel, message_id, owner_id):
        await asyncio.sleep(300)  # 5 minutes
        try:
            msg = await channel.fetch_message(message_id)
            if msg:
                await safe_delete(msg)
        except:
            pass
        # Reset du skill et du fake_spawn_id
        supabase.table("reiatsu").update({
            "fake_spawn_id": None,
            "active_skill": False
        }).eq("user_id", owner_id).execute()

    async def _spawn_faux_reiatsu(self, channel: discord.TextChannel):
        players = supabase.table("reiatsu").select("*").eq("classe", "Illusionniste").execute()
        for player in players.data:
            if player.get("active_skill") and not player.get("fake_spawn_id"):
                await self._spawn_message(channel, guild_id=None, is_fake=True, owner_id=int(player["user_id"]))

    # ───────────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "💠" or payload.user_id == self.bot.user.id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        user = guild.get_member(payload.user_id)
        if not channel or not user:
            return

        # Vérification faux Reiatsu
        players = supabase.table("reiatsu").select("*").eq("classe", "Illusionniste").execute()
        for p in players.data:
            fake_id = p.get("fake_spawn_id")
            if fake_id and payload.message_id == int(fake_id):
                if user.id != int(p["user_id"]):
                    owner = guild.get_member(int(p["user_id"]))
                    if owner:
                        gain = 50
                        owner_data = supabase.table("reiatsu").select("points").eq("user_id", owner.id).execute()
                        new_total = (owner_data.data[0]["points"] if owner_data.data else 0) + gain
                        supabase.table("reiatsu").update({
                            "points": new_total,
                            "fake_spawn_id": None,
                            "active_skill": False
                        }).eq("user_id", owner.id).execute()
                        await safe_send(channel, f"🎭 {user.mention} a absorbé un **faux Reiatsu** ! {owner.mention} gagne **+{gain}** points !")
                    try:
                        msg = await channel.fetch_message(payload.message_id)
                        await safe_delete(msg)
                    except:
                        pass
                return

        # Vérification Reiatsu normal
        conf_data = supabase.table("reiatsu_config").select("*").eq("guild_id", payload.guild_id).execute()
        if not conf_data.data:
            return
        conf = conf_data.data[0]
        if not conf.get("is_spawn") or payload.message_id != int(conf.get("message_id")):
            return

        gain = SUPER_REIATSU_GAIN if random.randint(1,100) <= SUPER_REIATSU_CHANCE else NORMAL_REIATSU_GAIN
        user_data = supabase.table("reiatsu").select("points").eq("user_id", user.id).execute()
        new_total = (user_data.data[0]["points"] if user_data.data else 0) + gain
        supabase.table("reiatsu").update({"points": new_total}).eq("user_id", user.id).execute()
        await safe_send(channel, f"💠 {user.mention} a absorbé un Reiatsu ! +{gain} points !")

        spawn_speed = conf.get("spawn_speed") or DEFAULT_SPAWN_SPEED
        min_delay, max_delay = SPAWN_SPEED_RANGES.get(spawn_speed, SPAWN_SPEED_RANGES[DEFAULT_SPAWN_SPEED])
        new_delay = random.randint(min_delay, max_delay)
        supabase.table("reiatsu_config").update({
            "is_spawn": False,
            "message_id": None,
            "spawn_delay": new_delay
        }).eq("guild_id", payload.guild_id).execute()
        try:
            msg_id = conf.get("message_id")
            if msg_id:
                msg = await channel.fetch_message(int(msg_id))
                await safe_delete(msg)
        except:
            pass

# ───────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ───────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuSpawner(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)

