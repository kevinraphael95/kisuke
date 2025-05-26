import discord
from discord.ext import commands
from supabase_client import supabase

class ReiatsuCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reiatsu", aliases=["rts"], help="Affiche le score de Reiatsu d'un membre (ou soi-même).")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 Cooldown 3s
    async def reiatsu(self, ctx, member: discord.Member = None):
        user = member or ctx.author
        data = supabase.table("reiatsu").select("points").eq("user_id", str(user.id)).execute()

        if data.data:
            points = data.data[0]["points"]
        else:
            points = 0

        await ctx.send(f"💠 {user.mention} a **{points}** points de Reiatsu.")


# Chargement automatique
async def setup(bot):
    cog = ReiatsuCommand(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
