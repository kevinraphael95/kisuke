import discord
from discord.ext import commands
from supabase_client import supabase

class SetReiatsuCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setreiatsu", aliases=["setrts"], help="Définit le salon actuel comme le salon Reiatsu. (Admin uniquement)")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 Cooldown 3s
    @commands.has_permissions(administrator=True)
    async def setreiatsu(self, ctx):
        channel_id = ctx.channel.id
        guild_id = ctx.guild.id

        # Vérifie si une config existe déjà
        data = supabase.table("reiatsu_config").select("id").eq("guild_id", str(guild_id)).execute()
        if data.data:
            supabase.table("reiatsu_config").update({"channel_id": str(channel_id)}).eq("guild_id", str(guild_id)).execute()
        else:
            supabase.table("reiatsu_config").insert({
                "guild_id": str(guild_id),
                "channel_id": str(channel_id)
            }).execute()

        await ctx.send(f"💠 Le salon actuel ({ctx.channel.mention}) est maintenant le salon Reiatsu.")

    @setreiatsu.before_invoke
    async def set_category(self, ctx):
        self.setreiatsu.category = "Reiatsu"

# Chargement automatique
async def setup(bot):
    await bot.add_cog(SetReiatsuCommand(bot))
