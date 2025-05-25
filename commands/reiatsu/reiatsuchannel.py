import discord
from discord.ext import commands
from supabase_client import supabase

class ReiatsuChannelCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reiatsuchannel", aliases=["rtschannel"], help="Affiche le salon configuré pour le spawn de Reiatsu. (Admin uniquement)")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 Cooldown 3s
    @commands.has_permissions(administrator=True)
    async def reiatsuchannel(self, ctx):
        guild_id = str(ctx.guild.id)

        data = supabase.table("reiatsu_config").select("channel_id").eq("guild_id", guild_id).execute()
        if data.data:
            channel_id = int(data.data[0]["channel_id"])
            channel = self.bot.get_channel(channel_id)
            if channel:
                await ctx.send(f"💠 Le salon configuré pour le spawn de Reiatsu est : {channel.mention}")
            else:
                await ctx.send("⚠️ Le salon configuré n'existe plus ou n'est pas accessible.")
        else:
            await ctx.send("❌ Aucun salon Reiatsu n’a encore été configuré avec `!setreiatsu`.")

    @reiatsuchannel.before_invoke
    async def set_category(self, ctx):
        self.reiatsuchannel.category = "Reiatsu"

# Chargement automatique
async def setup(bot):
    await bot.add_cog(ReiatsuChannelCommand(bot))
