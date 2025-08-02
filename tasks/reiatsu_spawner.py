# ──────────────────────────────────────────────────────────────#
# 📁 reiatsu_spawner.py — Spawn automatique de Reiatsu
# Objectif : Spawn un Reiatsu aléatoirement entre 30 min et 1h,
#           gérer le spawn, reset automatique en cas de blocage.
# Catégorie : Général
# Accès : Public
# ──────────────────────────────────────────────────────────────#

# ──────────────────────────────────────────────────────────────#
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────#
import discord
import random
import asyncio
from datetime import datetime, timezone
from discord.ext import commands, tasks
from supabase_client import supabase
from utils.discord_utils import safe_send, safe_add_reaction

# ──────────────────────────────────────────────────────────────#
# 🛠️ COG ReiatsuSpawner
# ──────────────────────────────────────────────────────────────#
class ReiatsuSpawner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spawn_task.start()

    def cog_unload(self):
        self.spawn_task.cancel()

    @tasks.loop(seconds=60)
    async def spawn_task(self):
        """Tâche qui tourne toutes les 60 secondes pour vérifier si on doit spawn un Reiatsu."""
        if not getattr(self.bot, "is_main_instance", True):
            # Évite les doublons si plusieurs instances du bot tournent
            return

        now_ts = datetime.now(timezone.utc).timestamp()

        try:
            configs = supabase.table("reiatsu_config").select("*").execute()
        except Exception as e:
            print(f"[Supabase] ❌ Erreur récupération configs: {e}")
            return

        for conf in configs.data:
            guild_id = conf["guild_id"]
            channel_id = conf.get("channel_id")
            if not channel_id:
                print(f"[Reiatsu] ⚠️ Pas de channel défini pour guild {guild_id}")
                continue

            en_attente = conf.get("en_attente", False)
            delay_min = conf.get("delay_minutes", 30)
            delay_sec = delay_min * 60

            last_spawn_str = conf.get("last_spawn_at")
            try:
                last_spawn_ts = datetime.fromisoformat(last_spawn_str).replace(tzinfo=timezone.utc).timestamp() if last_spawn_str else 0
            except Exception:
                last_spawn_ts = 0

            elapsed = now_ts - last_spawn_ts

            # Si blocage : Reiatsu en attente depuis plus de 5 minutes, reset forcé
            if en_attente and elapsed > 300:
                print(f"[Reiatsu] 🧨 Blocage détecté pour guild {guild_id}, reset en_attente")
                try:
                    supabase.table("reiatsu_config").update({
                        "en_attente": False,
                        "spawn_message_id": None
                    }).eq("guild_id", guild_id).execute()
                except Exception as e:
                    print(f"[Supabase] ❌ Erreur reset en_attente: {e}")
                en_attente = False  # On reset le flag localement

            # Spawn si pas en attente et délai écoulé
            if not en_attente and elapsed >= delay_sec:
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    print(f"[Reiatsu] ❌ Channel introuvable pour guild {guild_id}")
                    continue

                embed = discord.Embed(
                    title="💠 Un Reiatsu sauvage apparaît !",
                    description="Cliquez sur la réaction 💠 pour l'absorber.",
                    color=discord.Color.purple()
                )

                message = None
                for attempt in range(3):
                    try:
                        message = await safe_send(channel, embed=embed)
                        await safe_add_reaction(message, "💠")
                        break
                    except Exception as e:
                        print(f"[Discord] Tentative spawn #{attempt+1} échouée: {e}")
                        await asyncio.sleep(3)

                if message is None:
                    print(f"[Reiatsu] ❌ Impossible de spawn Reiatsu dans guild {guild_id}")
                    continue

                # Mise à jour config : en attente, last_spawn_at et message_id
                try:
                    supabase.table("reiatsu_config").update({
                        "en_attente": True,
                        "last_spawn_at": datetime.now(timezone.utc).isoformat(),
                        "spawn_message_id": str(message.id)
                    }).eq("guild_id", guild_id).execute()
                    print(f"[Reiatsu] Spawn réussi dans guild {guild_id}")
                except Exception as e:
                    print(f"[Supabase] ❌ Erreur update config après spawn: {e}")

    @spawn_task.before_loop
    async def before_spawn_task(self):
        await self.bot.wait_until_ready()
        print("[ReiatsuSpawner] La tâche de spawn est prête et démarre.")

    @commands.command(name="force_reiatsu")
    @commands.has_permissions(administrator=True)
    async def force_reiatsu(self, ctx: commands.Context):
        """Commande admin pour forcer un spawn immédiat dans ce salon."""
        embed = discord.Embed(
            title="💠 Un Reiatsu sauvage apparaît (FORCÉ) !",
            description="Cliquez sur la réaction 💠 pour l'absorber.",
            color=discord.Color.red()
        )
        try:
            message = await safe_send(ctx.channel, embed=embed)
            await safe_add_reaction(message, "💠")
            await ctx.send("✅ Reiatsu forcé spawné avec succès.")
        except Exception as e:
            await ctx.send(f"❌ Erreur lors du spawn forcé : {e}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Gestion de la réaction sur le message de spawn."""
        if str(payload.emoji) != "💠" or payload.user_id == self.bot.user.id:
            return

        guild_id = str(payload.guild_id)
        try:
            conf_data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
        except Exception as e:
            print(f"[Supabase] ❌ Erreur récupération config: {e}")
            return

        if not conf_data.data:
            return
        conf = conf_data.data[0]

        # Vérifier si on est bien sur un spawn en attente et sur le bon message
        if not conf.get("en_attente") or str(payload.message_id) != conf.get("spawn_message_id"):
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        channel = guild.get_channel(payload.channel_id)
        user = guild.get_member(payload.user_id)
        if not channel or not user:
            return

        # Calcul du gain selon la classe et proba super Reiatsu
        is_super = random.randint(1, 100) == 1
        gain = 100 if is_super else 1

        user_id = str(user.id)
        try:
            user_data = supabase.table("reiatsu").select("classe", "points", "bonus5").eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[Supabase] ❌ Erreur récupération user: {e}")
            return

        if user_data.data:
            classe = user_data.data[0].get("classe", "Travailleur")
            current_points = user_data.data[0]["points"]
            bonus5 = user_data.data[0].get("bonus5", 0) or 0
        else:
            classe = "Travailleur"
            current_points = 0
            bonus5 = 0

        # Ajustement selon la classe (exemple simple)
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

        new_points = current_points + gain

        # Mise à jour ou insertion utilisateur
        try:
            if user_data.data:
                supabase.table("reiatsu").update({
                    "points": new_points,
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
            print(f"[Supabase] ❌ Erreur update user: {e}")

        # Retirer les réactions du message pour bloquer les autres réactions
        try:
            msg = await channel.fetch_message(payload.message_id)
            await msg.clear_reactions()
        except Exception as e:
            print(f"[Discord] ❌ Erreur clear réactions: {e}")

        # Message de retour selon réussite
        if is_super:
            await safe_send(channel, f"🌟 {user.mention} a absorbé un **Super Reiatsu** et gagné **+{gain}** reiatsu !")
        else:
            if classe == "Parieur" and gain == 0:
                await safe_send(channel, f"🎲 {user.mention} a tenté d’absorber un reiatsu mais a raté (passif Parieur) !")
            else:
                await safe_send(channel, f"💠 {user.mention} a absorbé le Reiatsu et gagné **+{gain}** reiatsu !")

        # Reset config pour permettre un nouveau spawn aléatoire entre 30 et 60 min
        try:
            new_delay = random.randint(30, 60)
            supabase.table("reiatsu_config").update({
                "en_attente": False,
                "spawn_message_id": None,
                "delay_minutes": new_delay
            }).eq("guild_id", guild_id).execute()
        except Exception as e:
            print(f"[Supabase] ❌ Erreur reset config après absorption: {e}")

# ──────────────────────────────────────────────────────────────#
# 🔌 Setup automatique du Cog
# ──────────────────────────────────────────────────────────────#
async def setup(bot: commands.Bot):
    await bot.add_cog(ReiatsuSpawner(bot))
