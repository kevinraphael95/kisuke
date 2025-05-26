import discord
from discord.ext import commands
from supabase_client import supabase
from datetime import datetime
import random

class SetReiatsuCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setreiatsu", aliases=["setrts"], help="Définit le salon actuel comme le salon Reiatsu. (Admin uniquement)")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def setreiatsu(self, ctx):
        channel_id = ctx.channel.id
        guild_id = str(ctx.guild.id)
        now_iso = datetime.utcnow().isoformat()

        # Délai initial entre 30 et 90 minutes
        delay = random.randint(1800, 5400)

        data = supabase.table("reiatsu_config").select("id").eq("guild_id", guild_id).execute()
        if data.data:
            # Mise à jour config existante
            supabase.table("reiatsu_config").update({
                "channel_id": str(channel_id),
                "last_spawn_at": now_iso,
                "delay_minutes": delay,
                "en_attente": False
            }).eq("guild_id", guild_id).execute()
        else:
            # Nouvelle config
            supabase.table("reiatsu_config").insert({
                "guild_id": guild_id,
                "channel_id": str(channel_id),
                "last_spawn_at": now_iso,
                "delay_minutes": delay,
                "en_attente": False
            }).execute()

        await ctx.send(f"💠 Le salon actuel ({ctx.channel.mention}) est maintenant le salon Reiatsu.")

    @setreiatsu.before_invoke
    async def set_category(self, ctx):
        self.setreiatsu.category = "Reiatsu"

# Chargement automatique
async def setup(bot):
    await bot.add_cog(SetReiatsuCommand(bot))
