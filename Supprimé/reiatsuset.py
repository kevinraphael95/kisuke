# ──────────────────────────────────────────────────────────────
# 📁 REIATSU - CONFIGURATION DU SALON
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from supabase_client import supabase
from datetime import datetime
import random

# ──────────────────────────────────────────────────────────────
# 🔧 COG : SetReiatsuCommand
# ──────────────────────────────────────────────────────────────
class SetReiatsuCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot  # 🔌 Référence au bot

    # ──────────────────────────────────────────────────────────
    # ⚙️ COMMANDE : !setreiatsu
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="reiatsuset",
        aliases=["rtsset"],
        help="💠 Définit le salon actuel comme le salon Reiatsu. (Admin uniquement)"
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🧊 Cooldown 3s
    @commands.has_permissions(administrator=True)  # 🛡️ Réservé aux admins
    async def setreiatsu(self, ctx: commands.Context):
        channel_id = ctx.channel.id
        guild_id = str(ctx.guild.id)
        now_iso = datetime.utcnow().isoformat()  # 🕒 Heure actuelle

        # 🎲 Délai initial aléatoire entre 30 et 90 minutes
        delay = random.randint(1800, 5400)

        # 📦 Requête Supabase
        data = supabase.table("reiatsu_config") \
                       .select("id") \
                       .eq("guild_id", guild_id) \
                       .execute()

        if data.data:
            # 🔄 Mise à jour de la configuration existante
            supabase.table("reiatsu_config").update({
                "channel_id": str(channel_id),
                "last_spawn_at": now_iso,
                "delay_minutes": delay,
                "en_attente": False,
                "spawn_message_id": None
            }).eq("guild_id", guild_id).execute()
        else:
            # ➕ Création d’une nouvelle configuration
            supabase.table("reiatsu_config").insert({
                "guild_id": guild_id,
                "channel_id": str(channel_id),
                "last_spawn_at": now_iso,
                "delay_minutes": delay,
                "en_attente": False,
                "spawn_message_id": None
            }).execute()

        # 📢 Confirmation
        await ctx.send(f"✅ Le salon actuel {ctx.channel.mention} est désormais configuré pour le spawn de Reiatsu.")

    # 🏷️ Attribution de la catégorie
    def cog_load(self):
        self.setreiatsu.category = "Reiatsu"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(SetReiatsuCommand(bot))
    print("✅ Cog chargé : SetReiatsuCommand (catégorie = Reiatsu)")
