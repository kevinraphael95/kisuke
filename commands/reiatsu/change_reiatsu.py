import discord
from discord.ext import commands
from supabase_client import supabase

class SetReiatsuPoints(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="change_reiatsu", aliases = ["changerts"], help="(Admin) Modifie le score Reiatsu d'un membre.")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def change_reiatsu(self, ctx, member: discord.Member, points: int):
        if points < 0:
            await ctx.send("❌ Le score doit être positif.")
            return

        user_id = str(member.id)
        data = supabase.table("reiatsu").select("id").eq("user_id", user_id).execute()

        if data.data:
            supabase.table("reiatsu").update({"points": points}).eq("user_id", user_id).execute()
        else:
            supabase.table("reiatsu").insert({
                "user_id": user_id,
                "username": member.name,
                "points": points
            }).execute()

        await ctx.send(f"✅ Le score de {member.mention} est maintenant de **{points}** points.")

# Chargement automatique
async def setup(bot):
    cog = SetReiatsuPoints(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
