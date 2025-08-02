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
from supabase_client import supabase
from utils.discord_utils import safe_send, safe_add_reaction

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
        if not getattr(self.bot, "is_main_instance", True):
            return

        now = int(time.time())

        try:
            configs = supabase.table("reiatsu_config").select("*").execute()
        except Exception as e:
            print(f"[Supabase] Erreur récupération config : {e}")
            return

        for conf in configs.data:
            guild_id = conf["guild_id"]
            channel_id = conf.get("channel_id")
            en_attente = conf.get("en_attente", False)
            delay = (conf.get("delay_minutes") or 30) * 60
            last_spawn_str = conf.get("last_spawn_at")
            last_spawn = parser.parse(last_spawn_str).timestamp() if last_spawn_str else 0
            temps_ecoule = now - int(last_spawn)

            if not channel_id:
                continue

            # 🚨 Forçage du spawn si bloqué (message "un reiatsu va bientôt apparaître" bloqué +5 min)
            if en_attente and temps_ecoule > 5 * 60:
                print(f"[Reiatsu] Blocage détecté — Forçage du spawn pour {guild_id}")
                en_attente = False
                try:
                    supabase.table("reiatsu_config").update({
                        "en_attente": False,
                        "spawn_message_id": None
                    }).eq("guild_id", guild_id).execute()
                except Exception as e:
                    print(f"[Supabase] Erreur reset en_attente : {e}")
                # on continue vers le spawn forcé

            if en_attente or temps_ecoule < delay:
                continue

            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                continue

            embed = discord.Embed(
                title="💠 Un Reiatsu sauvage apparaît !",
                description="Cliquez sur la réaction 💠 pour l'absorber.",
                color=discord.Color.purple()
            )

            try:
                message = await safe_send(channel, embed=embed)
                await safe_add_reaction(message, "💠")
            except Exception as e:
                print(f"[Erreur] Envoi ou réaction du Reiatsu : {e}")
                continue

            try:
                supabase.table("reiatsu_config").update({
                    "en_attente": True,
                    "last_spawn_at": datetime.utcnow().isoformat(),
                    "spawn_message_id": str(message.id)
                }).eq("guild_id", guild_id).execute()
            except Exception as e:
                print(f"[Supabase] Erreur update spawn : {e}")

    # ──────────────────────────────────────────────────────────
    # 🎯 ÉVÉNEMENT : Réaction au spawn
    # ──────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "💠" or payload.user_id == self.bot.user.id:
            return

        guild_id = str(payload.guild_id)
        try:
            conf_data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
        except Exception as e:
            print(f"[Supabase] Erreur récupération conf : {e}")
            return

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

        is_super = random.randint(1, 100) == 1
        gain = 100 if is_super else 1
        user_id = str(user.id)

        try:
            user_data = supabase.table("reiatsu").select("classe", "points", "bonus5").eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[Supabase] Erreur récupération reiatsu : {e}")
            return

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
            elif classe == "Travailleur":
                bonus5 += 1
                if bonus5 >= 5:
                    gain = 6
                    bonus5 = 0
        else:
            bonus5 = 0

        new_total = current_points + gain

        try:
            if user_data.data:
                supabase.table("reiatsu").update({
                    "points": new_total,
                    "bonus5": bonus5,
                    "username": user.name
                }).eq("user_id", user_id).execute()
            else:
                supabase.table("reiatsu").insert({
                    "user_id": user_id,
                    "username": user.name,
                    "points": gain,
                    "classe": "Travailleur",
                    "bonus5": 1
                }).execute()
        except Exception as e:
            print(f"[Supabase] Erreur mise à jour utilisateur : {e}")

        try:
            msg = await channel.fetch_message(payload.message_id)
            await msg.clear_reactions()
        except Exception as e:
            print(f"[Discord] Erreur suppression réactions : {e}")

        if is_super:
            await safe_send(channel, f"🌟 {user.mention} a absorbé un **Super Reiatsu** et gagné **+{gain}** reiatsu !")
        else:
            if classe == "Parieur" and gain == 0:
                await safe_send(channel, f"🎲 {user.mention} a tenté d’absorber un reiatsu mais a raté (passif Parieur) !")
            else:
                await safe_send(channel, f"💠 {user.mention} a absorbé le Reiatsu et gagné **+{gain}** reiatsu !")

        try:
            new_delay = random.randint(30, 90)
            supabase.table("reiatsu_config").update({
                "en_attente": False,
                "spawn_message_id": None,
                "delay_minutes": new_delay
            }).eq("guild_id", guild_id).execute()
        except Exception as e:
            print(f"[Supabase] Erreur reset config : {e}")

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ReiatsuSpawner(bot))
