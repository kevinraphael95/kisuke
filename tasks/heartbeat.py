# ────────────────────────────────────────────────────────────────────────────────
# 📌 heartbeat.py — Cog pour gérer le heartbeat avec stockage du salon en Supabase
# Objectif : Envoyer un message régulier pour garder le bot "alive" et stocker le salon
# Catégorie : Général
# Accès : Modérateur (commande setheartbeatchannel)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class HeartbeatCog(commands.Cog):
    """
    Cog heartbeat — Envoie un message toutes les 5 minutes dans un salon configuré.
    Le salon est stocké dans Supabase pour garder la config persistante.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.supabase = bot.supabase  # Assure-toi que bot.supabase est bien initialisé
        self.heartbeat_channel_id = None
        self.heartbeat_task.start()

    def cog_unload(self):
        self.heartbeat_task.cancel()

    @tasks.loop(minutes=5)
    async def heartbeat_task(self):
        if not self.heartbeat_channel_id:
            await self.load_heartbeat_channel()
        if self.heartbeat_channel_id:
            channel = self.bot.get_channel(self.heartbeat_channel_id)
            if channel:
                try:
                    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    await channel.send(f"💓 Heartbeat — Je suis toujours vivant ! ({now})")
                except Exception as e:
                    print(f"[Heartbeat] Erreur en envoyant le message : {e}")
            else:
                print("[Heartbeat] Salon non trouvé, pensez à reconfigurer le salon heartbeat.")

    @heartbeat_task.before_loop
    async def before_heartbeat(self):
        await self.bot.wait_until_ready()
        await self.load_heartbeat_channel()

    async def load_heartbeat_channel(self):
        try:
            resp = self.supabase.table("bot_settings").select("value").eq("key", "heartbeat_channel_id").execute()
            if resp.data and len(resp.data) > 0:
                val = resp.data[0]["value"]
                if val.isdigit():
                    self.heartbeat_channel_id = int(val)
                    print(f"[Heartbeat] Salon heartbeat chargé depuis Supabase : {self.heartbeat_channel_id}")
                else:
                    print("[Heartbeat] Valeur heartbeat_channel_id invalide en base.")
            else:
                print("[Heartbeat] Pas de salon heartbeat configuré en base.")
        except Exception as e:
            print(f"[Heartbeat] Erreur lecture Supabase : {e}")

    @commands.command(
        name="setheartbeatchannel",
        help="Définit le salon où envoyer le heartbeat toutes les 5 minutes.",
        description="Commande admin pour changer le salon heartbeat."
    )
    @commands.has_permissions(administrator=True)
    async def setheartbeatchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        self.heartbeat_channel_id = channel.id
        try:
            self.supabase.table("bot_settings").upsert({
                "key": "heartbeat_channel_id",
                "value": str(channel.id)
            }).execute()
            await ctx.send(f"✅ Salon heartbeat mis à jour : {channel.mention}")
            print(f"[Heartbeat] Salon heartbeat changé : {channel.id}")
        except Exception as e:
            await ctx.send("❌ Erreur lors de la sauvegarde en base.")
            print(f"[Heartbeat] Erreur Supabase save : {e}")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(HeartbeatCog(bot))
