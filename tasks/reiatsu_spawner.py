# ──────────────────────────────────────────────────────────────
# 📁 REIATSU - GESTION DU SPAWN
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
import random
import time
from datetime import datetime
from dateutil import parser

from discord.ext import commands, tasks
from utils.supabase_client import supabase

from utils.discord_utils import safe_send  # <-- Import fonctions sécurisées

# ──────────────────────────────────────────────────────────────
# 🔧 COG : ReiatsuSpawner
# ──────────────────────────────────────────────────────────────
class ReiatsuSpawner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spawn_loop.start()  # 🔁 Lancement automatique de la boucle

    def cog_unload(self):
        self.spawn_loop.cancel()  # 🛑 Arrêt de la boucle à l’unload

    # ──────────────────────────────────────────────────────────
    # ⏲️ TÂCHE : spawn_loop — toutes les 60 secondes
    # ──────────────────────────────────────────────────────────
    @tasks.loop(seconds=60)
    async def spawn_loop(self):
        await self.bot.wait_until_ready()

        # 🔒 Ne fait tourner la tâche que sur l'instance principale
        if not getattr(self.bot, "is_main_instance", True):
            return

        now = int(time.time())

        # 📦 Récupère la config des serveurs
        configs = supabase.table("reiatsu_config").select("*").execute()

        for conf in configs.data:
            guild_id = conf["guild_id"]
            channel_id = conf.get("channel_id")
            en_attente = conf.get("en_attente", False)
            delay = conf.get("delay_minutes") or 1800

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

            # ✨ Envoie du message de spawn
            embed = discord.Embed(
                title="💠 Un Reiatsu sauvage apparaît !",
                description="Cliquez sur la réaction 💠 pour l'absorber.",
                color=discord.Color.purple()
            )
            message = await safe_send(channel, embed=embed)  # <-- safe_send utilisé ici
            await message.add_reaction("💠")

            # 💾 Mise à jour de l'état
            supabase.table("reiatsu_config").update({
                "en_attente": True,
                "last_spawn_at": datetime.utcnow().isoformat(),
                "spawn_message_id": str(message.id)
            }).eq("guild_id", guild_id).execute()

    # ──────────────────────────────────────────────────────────
    # 🎯 ÉVÉNEMENT : Réaction au spawn
    # ──────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "💠" or payload.user_id == self.bot.user.id:
            return

        guild_id = str(payload.guild_id)
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

        # 🎲 Détermine si c'est un Super Reiatsu (1% de chance)
        is_super = random.randint(1, 100) == 1
        gain = 100 if is_super else 1

        user_id = str(user.id)
        # Récupère classe, points et bonus5
        user_data = supabase.table("reiatsu").select("classe", "points", "bonus5").eq("user_id", user_id).execute()
        if user_data.data:
            classe = user_data.data[0].get("classe")
            current_points = user_data.data[0]["points"]
            bonus5 = user_data.data[0].get("bonus5", 0) or 0
        else:
            classe = "Travailleur"
            current_points = 0
            bonus5 = 0

        # Gestion des passifs — uniquement si ce n'est PAS un Super Reiatsu
        if not is_super:
            if classe == "Absorbeur":
                gain += 5
            elif classe == "Parieur":
                if random.random() < 0.5:
                    gain = 0
                else:
                    gain = random.randint(5, 12)
            # Passif Travailleur
            if classe == "Travailleur":
                bonus5 += 1
                if bonus5 >= 5:
                    gain = 6
                    bonus5 = 0
        else:
            # Si Super Reiatsu, on ne compte pas dans bonus5
            bonus5 = 0

        new_total = current_points + gain

        # Mise à jour ou insertion avec mise à jour bonus5
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
                "classe": "Travailleur",
                "bonus5": 1
            }).execute()


        # Message de confirmation
        if is_super:
            await safe_send(channel, f"🌟 {user.mention} a absorbé un **Super Reiatsu** et gagné **+{gain}** reiatsu !")
        else:
            if classe == "Parieur" and gain == 0:
                await safe_send(channel, f"🎲 {user.mention} a tenté d’absorber un reiatsu mais a raté (passif Parieur) !")
            else:
                await safe_send(channel, f"💠 {user.mention} a absorbé le Reiatsu et gagné **+{gain}** reiatsu !")

        # 🔄 Réinitialisation de l’état de spawn
        new_delay = random.randint(1800, 5400)
        supabase.table("reiatsu_config").update({
            "en_attente": False,
            "spawn_message_id": None,
            "delay_minutes": new_delay
        }).eq("guild_id", guild_id).execute()


# ──────────────────────────────────────────────────────────────
# 🔌 SETUP AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ReiatsuSpawner(bot))
