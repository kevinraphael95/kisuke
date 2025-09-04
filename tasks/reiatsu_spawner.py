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

from discord.ext import commands, tasks
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_delete  # 🔒 utils protégés

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Paramètres globaux (facilement modifiables)
# ────────────────────────────────────────────────────────────────────────────────
SPAWN_LOOP_INTERVAL = 60             # Vérification toutes les 60s
SUPER_REIATSU_CHANCE = 1             # 1% de chance
SUPER_REIATSU_GAIN = 100
NORMAL_REIATSU_GAIN = 1

# Définition des plages de spawn selon la vitesse
SPAWN_SPEED_RANGES = {
    "Ultra_Rapide": (60, 300),       # 1-5 min
    "Rapide": (300, 1200),           # 5-20 min
    "Normal": (1800, 3600),          # 30-60 min
    "Lent": (18000, 36000)           # 5-10 h
}

DEFAULT_SPAWN_SPEED = "Normal"

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog : ReiatsuSpawner
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuSpawner(commands.Cog):
    """
    Gère le spawn automatique de Reiatsu et leur capture par les joueurs.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.locks = {}  # 🔒 locks par serveur pour éviter les races
        self.spawn_loop.start()

        # Vérification initiale après démarrage
        self.bot.loop.create_task(self._check_on_startup())

    def cog_unload(self):
        """Arrêt de la loop au déchargement du cog."""
        self.spawn_loop.cancel()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔄 Vérification au redémarrage
    # ────────────────────────────────────────────────────────────────────────────
    async def _check_on_startup(self):
        """Vérifie que les messages spawn encore marqués existent vraiment."""
        await self.bot.wait_until_ready()
        configs = supabase.table("reiatsu_config").select("*").execute()

        for conf in configs.data:
            if not conf.get("en_attente") or not conf.get("spawn_message_id"):
                continue

            guild = self.bot.get_guild(int(conf["guild_id"]))
            if not guild:
                continue

            channel = guild.get_channel(int(conf.get("channel_id") or 0))
            if not channel:
                continue

            try:
                await channel.fetch_message(int(conf["spawn_message_id"]))
            except Exception:
                # ❌ Message introuvable → reset état
                supabase.table("reiatsu_config").update({
                    "en_attente": False,
                    "spawn_message_id": None
                }).eq("guild_id", conf["guild_id"]).execute()
                print(f"[RESET] Reiatsu fantôme nettoyé pour guild {conf['guild_id']}")

    # ────────────────────────────────────────────────────────────────────────────
    # ⏲️ Tâche périodique — vérifie les spawns toutes les SPAWN_LOOP_INTERVAL
    # ────────────────────────────────────────────────────────────────────────────
    @tasks.loop(seconds=SPAWN_LOOP_INTERVAL)
    async def spawn_loop(self):
        await self.bot.wait_until_ready()
        if not getattr(self.bot, "is_main_instance", True):
            return  # 🔒 évite multi-instances

        try:
            await self._spawn_tick()
        except Exception as e:
            print(f"[ERREUR spawn_loop] {e}")

    async def _spawn_tick(self):
        """Vérifie chaque config serveur pour savoir si un spawn doit apparaître."""
        now = int(time.time())
        configs = supabase.table("reiatsu_config").select("*").execute()

        for conf in configs.data:
            guild_id = conf["guild_id"]
            channel_id = conf.get("channel_id")
            en_attente = conf.get("en_attente", False)

            # Récupère la vitesse et la plage correspondante
            spawn_speed = conf.get("spawn_speed") or DEFAULT_SPAWN_SPEED
            min_delay, max_delay = SPAWN_SPEED_RANGES.get(spawn_speed, SPAWN_SPEED_RANGES[DEFAULT_SPAWN_SPEED])
            
            # Si un delay exact est défini, on l'utilise
            delay = conf.get("spawn_delay") or random.randint(min_delay, max_delay)

            if not channel_id or en_attente:
                continue

            last_spawn_str = conf.get("last_spawn_at")
            should_spawn = not last_spawn_str or (
                now - int(parser.parse(last_spawn_str).timestamp()) >= delay
            )
            if not should_spawn:
                continue

            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                continue

            await self._spawn_message(channel, guild_id)

    async def _spawn_message(self, channel, guild_id):
        """Envoie le message de spawn et met à jour la DB."""
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
            pass  # ⚠️ si rate limit ou erreur

        supabase.table("reiatsu_config").update({
            "en_attente": True,
            "last_spawn_at": datetime.utcnow().isoformat(timespec="seconds"),
            "spawn_message_id": str(message.id)
        }).eq("guild_id", guild_id).execute()

    # ────────────────────────────────────────────────────────────────────────────
    # 🎯 Événement : Réaction à un spawn
    # ────────────────────────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "💠" or payload.user_id == self.bot.user.id:
            return

        guild_id = str(payload.guild_id)
        if guild_id not in self.locks:
            self.locks[guild_id] = asyncio.Lock()

        async with self.locks[guild_id]:  # 🔒 anti-race
            conf_data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
            if not conf_data.data:
                return

            conf = conf_data.data[0]
            if not conf.get("en_attente") or str(payload.message_id) != conf.get("spawn_message_id"):
                return

            guild = self.bot.get_guild(payload.guild_id)
            channel = guild.get_channel(payload.channel_id)
            user = guild.get_member(payload.user_id)
            if not channel or not user:
                return

            gain, is_super, bonus5, classe, new_total = self._calculate_gain(user.id)

            # 💾 Update DB joueur
            self._update_player(user, gain, bonus5, new_total, classe)

            # 📢 Message feedback
            await self._send_feedback(channel, user, gain, is_super, classe)

            # 🔄 Reset état + nouveau délai selon spawn_speed
            spawn_speed = conf.get("spawn_speed") or DEFAULT_SPAWN_SPEED
            min_delay, max_delay = SPAWN_SPEED_RANGES.get(spawn_speed, SPAWN_SPEED_RANGES[DEFAULT_SPAWN_SPEED])
            new_delay = random.randint(min_delay, max_delay)
            supabase.table("reiatsu_config").update({
                "en_attente": False,
                "spawn_message_id": None,
                "spawn_delay": new_delay
            }).eq("guild_id", guild_id).execute()

            # 🧹 Suppression du message de spawn
            try:
                message = await channel.fetch_message(int(conf["spawn_message_id"]))
                await safe_delete(message)
            except Exception:
                pass  # si déjà supprimé ou introuvable

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Utilitaires internes
    # ────────────────────────────────────────────────────────────────────────────
    def _calculate_gain(self, user_id):
        """Calcule le gain en fonction de la classe et des passifs."""
        is_super = random.randint(1, 100) <= SUPER_REIATSU_CHANCE
        gain = SUPER_REIATSU_GAIN if is_super else NORMAL_REIATSU_GAIN

        user_data = supabase.table("reiatsu").select("classe", "points", "bonus5").eq("user_id", str(user_id)).execute()
        if user_data.data:
            classe = user_data.data[0].get("classe")
            current_points = user_data.data[0]["points"]
            bonus5 = user_data.data[0].get("bonus5", 0) or 0
        else:
            classe = "Travailleur"
            current_points = 0
            bonus5 = 0

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
        """Met à jour ou insère le joueur dans la DB."""
        user_id = str(user.id)
        user_data = supabase.table("reiatsu").select("user_id").eq("user_id", user_id).execute()
        if user_data.data:
            supabase.table("reiatsu").update({
                "points": new_total,
                "bonus5": bonus5
            }).eq("user_id", user_id).execute()
        else:
            supabase.table("reiatsu").insert({
                "user_id": user_id,
                "username": user.name,
                "points": gain,
                "classe": classe,
                "bonus5": 1
            }).execute()

    async def _send_feedback(self, channel, user, gain, is_super, classe):
        """Envoie un message de confirmation après capture."""
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
    cog = ReiatsuSpawner(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
