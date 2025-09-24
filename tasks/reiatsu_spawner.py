# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu_spawner.py — Gestion du spawn des Reiatsu
# Objectif : Gérer l’apparition et la capture des Reiatsu sur les serveurs
# Catégorie : Reiatsu / RPG
# Accès : Tous
# Cooldown : Spawn auto toutes les X minutes (configurable par serveur)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
import random
import time
import asyncio
from datetime import datetime
from dateutil import parser
from pathlib import Path
from discord.ext import commands, tasks
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_delete
import json

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Paramètres globaux (facilement modifiables)
# ────────────────────────────────────────────────────────────────────────────────
CONFIG_PATH = Path("data/reiatsu_config.json")
with CONFIG_PATH.open("r", encoding="utf-8") as f:
    CONFIG = json.load(f)

SPAWN_LOOP_INTERVAL = CONFIG.get("SPAWN_LOOP_INTERVAL", 10)
SUPER_REIATSU_CHANCE = CONFIG.get("SUPER_REIATSU_CHANCE", 5)
SUPER_REIATSU_GAIN = CONFIG.get("SUPER_REIATSU_GAIN", 50)
NORMAL_REIATSU_GAIN = CONFIG.get("NORMAL_REIATSU_GAIN", 10)
SPAWN_SPEED_RANGES = CONFIG.get("SPAWN_SPEED_RANGES", {"Normal": [60, 120]})
DEFAULT_SPAWN_SPEED = CONFIG.get("DEFAULT_SPAWN_SPEED", "Normal")
CLASSES = CONFIG.get("CLASSES", [])

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog : ReiatsuSpawner
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuSpawner(commands.Cog):
    """
    Gère le spawn automatique de Reiatsu et le faux Reiatsu des Illusionnistes.
    Chaque joueur Illusionniste peut avoir un faux Reiatsu actif.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.locks = {}
        print("⚡ Initialisation du ReiatsuSpawner…")
        self.spawn_loop.start()
        self.bot.loop.create_task(self._check_on_startup())

    def cog_unload(self):
        """Arrêt de la loop au déchargement du cog."""
        self.spawn_loop.cancel()

    async def _check_on_startup(self):
        """Vérifie que les messages spawn encore marqués existent vraiment."""
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
                }).eq("guild_id", conf["guild_id"]).execute()
                print(f"[RESET] Reiatsu fantôme nettoyé pour guild {conf['guild_id']}")

    @tasks.loop(seconds=SPAWN_LOOP_INTERVAL)
    async def spawn_loop(self):
        await self.bot.wait_until_ready()
        if not getattr(self.bot, "is_main_instance", True):
            print("[spawn_loop] Instance secondaire, spawn désactivé")
            return
        try:
            print(f"[DEBUG] spawn_loop tick — {datetime.utcnow().isoformat()}")
            await self._spawn_tick()
        except Exception as e:
            print(f"[ERREUR spawn_loop] {e}")

    async def _spawn_tick(self):
        now = int(time.time())
        configs = supabase.table("reiatsu_config").select("*").execute()
        for conf in configs.data:
            guild_id = conf["guild_id"]
            channel_id = conf.get("channel_id")
            if not channel_id:
                continue

            last_spawn_str = conf.get("last_spawn_at")
            spawn_speed = conf.get("spawn_speed") or DEFAULT_SPAWN_SPEED
            min_delay, max_delay = SPAWN_SPEED_RANGES.get(spawn_speed, SPAWN_SPEED_RANGES[DEFAULT_SPAWN_SPEED])
            delay = conf.get("spawn_delay") or random.randint(min_delay, max_delay)
            should_spawn = not last_spawn_str or (now - int(parser.parse(last_spawn_str).timestamp()) >= delay)

            print(f"[DEBUG] Guild {guild_id} — should_spawn={should_spawn} — is_spawn={conf.get('is_spawn')}")

            if should_spawn and not conf.get("is_spawn", False):
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    await self._spawn_message(channel, guild_id)

            channel = self.bot.get_channel(int(channel_id))
            if channel:
                await self._spawn_faux_reiatsu(channel)

    async def _spawn_message(self, channel, guild_id):
        embed = discord.Embed(
            title="💠 Un Reiatsu sauvage apparaît !",
            description="Cliquez sur la réaction 💠 pour l'absorber.",
            color=discord.Color.purple()
        )
        message = await safe_send(channel, embed=embed)
        if not message:
            return
        try:
            await message.add_reaction("💠")
        except discord.HTTPException:
            pass
        supabase.table("reiatsu_config").update({
            "is_spawn": True,
            "last_spawn_at": datetime.utcnow().isoformat(timespec="seconds"),
            "message_id": str(message.id)
        }).eq("guild_id", guild_id).execute()
        print(f"[SPAWN] Reiatsu spawné en guild {guild_id} message {message.id}")

    async def _spawn_faux_reiatsu(self, channel: discord.TextChannel):
        players = supabase.table("reiatsu").select("*").eq("classe", "Illusionniste").execute()
        for player in players.data:
            if player.get("active_skill") and not player.get("fake_spawn_id"):
                embed = discord.Embed(
                    title="🎭 Un faux Reiatsu apparaît !",
                    description="Cliquez sur 💠 pour l'absorber… si vous osez !",
                    color=discord.Color.gold()
                )
                message = await safe_send(channel, embed=embed)
                if not message:
                    continue
                try:
                    await message.add_reaction("💠")
                except discord.HTTPException:
                    pass
                supabase.table("reiatsu").update({
                    "fake_spawn_id": str(message.id)
                }).eq("user_id", player["user_id"]).execute()
                print(f"[SPAWN] Faux Reiatsu pour Illusionniste {player['user_id']}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "💠" or payload.user_id == self.bot.user.id:
            return

        guild_id = str(payload.guild_id)
        if guild_id not in self.locks:
            self.locks[guild_id] = asyncio.Lock()

        async with self.locks[guild_id]:
            guild = self.bot.get_guild(payload.guild_id)
            channel = guild.get_channel(payload.channel_id)
            user = guild.get_member(payload.user_id)
            if not channel or not user:
                return

            # Faux Reiatsu (Illusionniste)
            players = supabase.table("reiatsu").select("*").eq("classe", "Illusionniste").execute()
            for p in players.data:
                fake_id = p.get("fake_spawn_id")
                if fake_id and str(payload.message_id) == fake_id:
                    owner = guild.get_member(int(p["user_id"]))
                    if owner:
                        owner_data = supabase.table("reiatsu").select("points").eq("user_id", p["user_id"]).single().execute()
                        if owner_data.data:
                            new_points = owner_data.data["points"] + 10
                            supabase.table("reiatsu").update({"points": new_points}).eq("user_id", p["user_id"]).execute()
                        await safe_send(channel, f"🎭 Le faux Reiatsu a été absorbé par {user.mention}... {owner.mention} gagne **+10** points !")
                    supabase.table("reiatsu").update({"fake_spawn_id": None}).eq("user_id", p["user_id"]).execute()
                    try:
                        await safe_delete(await channel.fetch_message(payload.message_id))
                    except Exception:
                        pass
                    return

            # Reiatsu normal
            conf_data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
            if not conf_data.data:
                return
            conf = conf_data.data[0]

            message_ok = True
            if conf.get("is_spawn") and conf.get("message_id"):
                try:
                    await channel.fetch_message(int(conf["message_id"]))
                except discord.NotFound:
                    supabase.table("reiatsu_config").update({
                        "is_spawn": False,
                        "message_id": None
                    }).eq("guild_id", guild_id).execute()
                    message_ok = False

            if not conf.get("is_spawn") or not message_ok:
                return
            if str(payload.message_id) != conf.get("message_id"):
                return

            gain, is_super, bonus5, classe, new_total = self._calculate_gain(user.id)
            self._update_player(user, gain, bonus5, new_total, classe)
            await self._send_feedback(channel, user, gain, is_super, classe)

            spawn_speed = conf.get("spawn_speed") or DEFAULT_SPAWN_SPEED
            min_delay, max_delay = SPAWN_SPEED_RANGES.get(spawn_speed, SPAWN_SPEED_RANGES[DEFAULT_SPAWN_SPEED])
            new_delay = random.randint(min_delay, max_delay)
            supabase.table("reiatsu_config").update({
                "is_spawn": False,
                "message_id": None,
                "spawn_delay": new_delay
            }).eq("guild_id", guild_id).execute()

            try:
                await safe_delete(await channel.fetch_message(int(conf.get("message_id"))))
            except Exception:
                pass

    # ────────────────────────────────────────────────────────────────────────────
    # Fonctions auxiliaires
    # ────────────────────────────────────────────────────────────────────────────
    def _calculate_gain(self, user_id):
        is_super = random.randint(1, 100) <= SUPER_REIATSU_CHANCE
        user_data = supabase.table("reiatsu").select("classe", "points", "bonus5").eq("user_id", str(user_id)).execute()
        if user_data.data:
            classe = user_data.data[0].get("classe")
            current_points = user_data.data[0]["points"]
            bonus5 = user_data.data[0].get("bonus5", 0) or 0
        else:
            classe = "Travailleur"
            current_points = 0
            bonus5 = 0

        gain = SUPER_REIATSU_GAIN if is_super else NORMAL_REIATSU_GAIN
        if not is_super:
            if classe == "Absorbeur":
                gain += 5
            elif classe == "Parieur":
                gain = 0 if random.random() < 0.5 else random.randint(5, 12)
            if classe == "Travailleur":
                bonus5 += 1
                if bonus5 >= 5:
                    gain = 6
                    bonus5 = 0
        else:
            bonus5 = 0

        return gain, is_super, bonus5, classe, current_points + gain

    def _update_player(self, user, gain, bonus5, new_total, classe):
        user_id = str(user.id)
        user_data = supabase.table("reiatsu").select("user_id").eq("user_id", user_id).execute()
        if user_data.data:
            supabase.table("reiatsu").update({"points": new_total, "bonus5": bonus5}).eq("user_id", user_id).execute()
        else:
            supabase.table("reiatsu").insert({
                "user_id": user_id,
                "username": user.name,
                "points": gain,
                "classe": classe,
                "bonus5": 1
            }).execute()

    async def _send_feedback(self, channel, user, gain, is_super, classe):
        if is_super:
            await safe_send(channel, f"🌟 {user.mention} a absorbé un **Super Reiatsu** et gagné **+{gain}** reiatsu !")
        else:
            if classe == "Parieur" and gain == 0:
                await safe_send(channel, f"🎲 {user.mention} a tenté d’absorber un reiatsu mais a raté (passif Parieur) !")
            else:
                await safe_send(channel, f"💠 {user.mention} a absorbé le Reiatsu et gagné **+{gain}** reiatsu !")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    print("⚡ Chargement du ReiatsuSpawner…")
    cog = ReiatsuSpawner(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
