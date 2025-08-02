# ──────────────────────────────────────────────────────────────
## 📁 reiatsu_spawner.py — Spawn automatique de Reiatsu
# Objectif :
#   - Spawn un Reiatsu aléatoirement entre 30 min et 1h
#   - Gérer le spawn, reset automatique en cas de blocage
#   - Forcer spawn si blocage > 5 minutes
# Catégorie : Général
# Accès : Public
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
## 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord                            # API Discord
import random                            # Tirage aléatoire
import asyncio                           # Gestion des tâches asynchrones et délais
from datetime import datetime, timezone # Dates et timestamps UTC standardisés
from discord.ext import commands, tasks # Cog, commandes, et boucle de tâche Discord

# Import Supabase (base de données)
from supabase_client import supabase

# Fonctions sécurisées (gèrent 429 / erreurs Discord)
from utils.discord_utils import safe_send, safe_add_reaction

# ──────────────────────────────────────────────────────────────
## 🛠️ COG : ReiatsuSpawner
# ──────────────────────────────────────────────────────────────
class ReiatsuSpawner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        # Référence au bot principal
        self.bot = bot
        
        # Démarrage de la tâche en boucle toutes les 60 secondes
        self.spawn_task.start()

    def cog_unload(self):
        # Stoppe la tâche proprement à la décharge du Cog
        self.spawn_task.cancel()

    # ───────────────────────────────────────────────
    @tasks.loop(seconds=60)
    async def spawn_task(self):
        """
        Tâche asynchrone qui s’exécute toutes les 60 secondes
        pour vérifier si on doit spawn un Reiatsu dans chaque guild configurée.
        """
        # Eviter spawn en double si plusieurs instances du bot tournent
        if not getattr(self.bot, "is_main_instance", True):
            return  # Quitte si pas l’instance principale

        # Timestamp actuel UTC en secondes (float)
        now_ts = datetime.now(timezone.utc).timestamp()

        # Récupération de toutes les configs Reiatsu (une par guild)
        try:
            configs = supabase.table("reiatsu_config").select("*").execute()
        except Exception as e:
            print(f"[Supabase] ❌ Erreur récupération configs: {e}")
            return

        # Parcours de toutes les configs guild par guild
        for conf in configs.data:
            guild_id = conf.get("guild_id")
            channel_id = conf.get("channel_id")
            
            # Verification canal texte configuré
            if not channel_id:
                print(f"[Reiatsu] ⚠️ Pas de channel défini pour guild {guild_id}")
                continue

            # Etat actuel : Reiatsu en attente d’absorption ?
            en_attente = conf.get("en_attente", False)
            delay_min = conf.get("delay_minutes", 30)  # Délai entre spawns (minutes)
            delay_sec = delay_min * 60                  # Conversion en secondes

            # Date/heure du dernier spawn stockée en ISO, ou 0 si jamais spawné
            last_spawn_str = conf.get("last_spawn_at")
            try:
                if last_spawn_str:
                    last_spawn_ts = datetime.fromisoformat(last_spawn_str).replace(tzinfo=timezone.utc).timestamp()
                else:
                    last_spawn_ts = 0
            except Exception:
                last_spawn_ts = 0

            # Temps écoulé depuis dernier spawn (en secondes)
            elapsed = now_ts - last_spawn_ts

            # --- Gestion du blocage ---
            # Si Reiatsu est en attente depuis plus de 5 minutes (300 sec)
            # => Reset forcé du flag pour débloquer le spawn
            if en_attente and elapsed > 300:
                print(f"[Reiatsu] 🧨 Blocage détecté (en_attente > 5min) pour guild {guild_id}, reset du flag.")
                try:
                    supabase.table("reiatsu_config").update({
                        "en_attente": False,
                        "spawn_message_id": None
                    }).eq("guild_id", guild_id).execute()
                except Exception as e:
                    print(f"[Supabase] ❌ Erreur reset en_attente: {e}")
                # Reset local aussi
                en_attente = False

            # --- Spawn normal ---
            # Si pas en attente et délai écoulé, spawn un nouveau Reiatsu
            if not en_attente and elapsed >= delay_sec:
                # Récupération du channel Discord via ID
                channel = self.bot.get_channel(int(channel_id))
                if not channel:
                    print(f"[Reiatsu] ❌ Channel introuvable pour guild {guild_id}")
                    continue

                # Création de l'embed pour le message Reiatsu
                embed = discord.Embed(
                    title="💠 Un Reiatsu sauvage apparaît !",
                    description="Cliquez sur la réaction 💠 pour l'absorber.",
                    color=discord.Color.purple()
                )

                message = None

                # Tentatives de spawn jusqu'à 3 fois en cas d'erreur Discord (ex: rate limit)
                for attempt in range(3):
                    try:
                        # Envoi du message embedé
                        message = await safe_send(channel, embed=embed)
                        # Ajout de la réaction d'absorption
                        await safe_add_reaction(message, "💠")
                        break  # Succès => sortie boucle
                    except Exception as e:
                        print(f"[Discord] Tentative spawn #{attempt+1} échouée: {e}")
                        await asyncio.sleep(3)  # Pause avant réessayer

                if message is None:
                    print(f"[Reiatsu] ❌ Impossible de spawn Reiatsu dans guild {guild_id} après 3 tentatives")
                    continue

                # Mise à jour de la config dans Supabase :
                #  - flag en attente = True (message présent, attente absorption)
                #  - date du dernier spawn = maintenant (ISO UTC)
                #  - id du message de spawn (pour suivi réactions)
                try:
                    supabase.table("reiatsu_config").update({
                        "en_attente": True,
                        "last_spawn_at": datetime.now(timezone.utc).isoformat(),
                        "spawn_message_id": str(message.id)
                    }).eq("guild_id", guild_id).execute()
                    print(f"[Reiatsu] Spawn réussi dans guild {guild_id} (message ID {message.id})")
                except Exception as e:
                    print(f"[Supabase] ❌ Erreur update config après spawn: {e}")

    # ───────────────────────────────────────────────
    @spawn_task.before_loop
    async def before_spawn_task(self):
        # Attend que le bot soit prêt avant de démarrer la boucle
        await self.bot.wait_until_ready()
        print("[ReiatsuSpawner] La tâche de spawn est prête et démarre.")

    # ───────────────────────────────────────────────
    @commands.command(name="force_reiatsu")
    @commands.has_permissions(administrator=True)
    async def force_reiatsu(self, ctx: commands.Context):
        """
        Commande admin pour forcer un spawn immédiat dans le salon actuel.
        Utile pour tester ou débloquer.
        """
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

    # ───────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Listener d’évènement déclenché quand une réaction est ajoutée.
        Gestion de la réaction 💠 pour absorption du Reiatsu.
        """
        # Ignorer les réactions autres que 💠 ou les réactions du bot lui-même
        if str(payload.emoji) != "💠" or payload.user_id == self.bot.user.id:
            return

        guild_id = str(payload.guild_id)

        # Récupération de la config Reiatsu actuelle
        try:
            conf_data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
        except Exception as e:
            print(f"[Supabase] ❌ Erreur récupération config: {e}")
            return

        if not conf_data.data:
            return  # Pas de config => on ignore

        conf = conf_data.data[0]

        # Vérifier que Reiatsu est en attente (spawn actif)
        # et que la réaction est sur le bon message
        if not conf.get("en_attente") or str(payload.message_id) != conf.get("spawn_message_id"):
            return

        # Récupération des objets Guild, Channel, User Discord
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        channel = guild.get_channel(payload.channel_id)
        user = guild.get_member(payload.user_id)
        if not channel or not user:
            return

        # --- Calcul du gain Reiatsu selon probabilité ---
        is_super = random.randint(1, 100) == 1  # 1% chance de super reiatsu
        gain = 100 if is_super else 1            # Gain fixe de base

        user_id = str(user.id)

        # Récupération des données utilisateur (classe, points, bonus)
        try:
            user_data = supabase.table("reiatsu").select("classe", "points", "bonus5").eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[Supabase] ❌ Erreur récupération user: {e}")
            return

        # Si user existe en base, on récupère ses stats
        if user_data.data:
            classe = user_data.data[0].get("classe", "Travailleur")
            current_points = user_data.data[0]["points"]
            bonus5 = user_data.data[0].get("bonus5", 0) or 0
        else:
            # Sinon, valeurs par défaut
            classe = "Travailleur"
            current_points = 0
            bonus5 = 0

        # Ajustement du gain selon la classe
        if not is_super:
            if classe == "Absorbeur":
                gain += 5  # Bonus fixe +5
            elif classe == "Parieur":
                # 50% chance de rien, sinon 5-12 points aléatoires
                gain = 0 if random.random() < 0.5 else random.randint(5, 12)
            elif classe == "Travailleur":
                # Bonus de 1 point accumulé, à 5 cumul = gain 6 points
                bonus5 += 1
                if bonus5 >= 5:
                    gain = 6
                    bonus5 = 0
        else:
            # Super reiatsu : reset bonus
            bonus5 = 0

        new_points = current_points + gain

        # Mise à jour ou insertion en base des points et bonus utilisateur
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

        # Retirer toutes les réactions pour bloquer d’autres absorptions
        try:
            msg = await channel.fetch_message(payload.message_id)
            await msg.clear_reactions()
        except Exception as e:
            print(f"[Discord] ❌ Erreur clear réactions: {e}")

        # Message retour selon réussite
        if is_super:
            await safe_send(channel, f"🌟 {user.mention} a absorbé un **Super Reiatsu** et gagné **+{gain}** reiatsu !")
        else:
            if classe == "Parieur" and gain == 0:
                await safe_send(channel, f"🎲 {user.mention} a tenté d’absorber un reiatsu mais a raté (passif Parieur) !")
            else:
                await safe_send(channel, f"💠 {user.mention} a absorbé le Reiatsu et gagné **+{gain}** reiatsu !")

        # Reset config pour permettre spawn aléatoire entre 30 et 60 minutes
        try:
            new_delay = random.randint(30, 60)
            supabase.table("reiatsu_config").update({
                "en_attente": False,
                "spawn_message_id": None,
                "delay_minutes": new_delay
            }).eq("guild_id", guild_id).execute()
        except Exception as e:
            print(f"[Supabase] ❌ Erreur reset config après absorption: {e}")

# ──────────────────────────────────────────────────────────────
## 🔌 Setup automatique du Cog
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ReiatsuSpawner(bot))

