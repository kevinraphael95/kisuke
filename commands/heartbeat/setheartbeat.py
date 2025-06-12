# ────────────────────────────────────────────────────────────────────────────────
# 📌 hsetheartbeat.py — Commande !setheartbeatchannel pour configurer le salon
# Objectif : Permettre aux admins de définir le salon où envoyer le heartbeat
# Catégorie : Heartbeat
# Accès : Modérateur (permission admin requise)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class HSetHeartbeat(commands.Cog):
    """
    Commande setheartbeatchannel pour définir le salon heartbeat.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.supabase = bot.supabase

    @commands.command(
        name="setheart",
        aliases=["sethb"],
        help="Définit le salon où envoyer le heartbeat toutes les 5 minutes.",
        description="Commande admin pour changer le salon heartbeat."
    )
    @commands.has_permissions(administrator=True)
    async def setheartbeatchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        try:
            self.supabase.table("bot_settings").upsert({
                "key": "heartbeat_channel_id",
                "value": str(channel.id)
            }).execute()

            # Mise à jour de la variable dans le Cog task si chargé
            heartbeat_cog = self.bot.get_cog("HeartbeatTask")
            if heartbeat_cog:
                heartbeat_cog.heartbeat_channel_id = channel.id

            await ctx.send(f"✅ Salon heartbeat mis à jour : {channel.mention}")
            print(f"[setheartbeatchannel] Salon heartbeat changé : {channel.id}")
        except Exception as e:
            await ctx.send("❌ Erreur lors de la sauvegarde en base.")
            print(f"[setheartbeatchannel] Erreur : {e}")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HSetHeartbeat(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Heartbeat"
    await bot.add_cog(cog)
    print("✅ Cog chargé : HSetHeartbeat (catégorie = Heartbeat)")
