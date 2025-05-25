import discord
import asyncio
from discord.ext import commands
from supabase_client import supabase

class SpawnReiatsuCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="spawnreiatsu", aliases=["spawnrts"], help="Force le spawn d’un Reiatsu dans le salon configuré. (Admin uniquement)")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 3s cooldown
    async def spawnreiatsu(self, ctx):
        guild_id = str(ctx.guild.id)

        # 🔁 Recherche du salon Reiatsu directement ici
        config = supabase.table("reiatsu_config").select("channel_id").eq("guild_id", guild_id).execute()
        if not config.data:
            await ctx.send("❌ Aucun salon Reiatsu n’a été configuré. Utilise `!setreiatsu`.")
            return

        channel_id = int(config.data[0]["channel_id"])
        channel = self.bot.get_channel(channel_id)

        if not channel:
            await ctx.send("⚠️ Le salon configuré n'existe plus ou n'est pas accessible.")
            return

        embed = discord.Embed(
            title="💠 Un Reiatsu sauvage apparaît !",
            description="Cliquez sur la réaction 💠 pour l'absorber.",
            color=discord.Color.purple()
        )
        message = await channel.send(embed=embed)
        await message.add_reaction("💠")

        def check(reaction, user):
            return (
                reaction.message.id == message.id and
                str(reaction.emoji) == "💠" and
                not user.bot
            )

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=10800.0, check=check)

            data = supabase.table("reiatsu").select("id", "points").eq("user_id", str(user.id)).execute()
            if data.data:
                current = data.data[0]["points"]
                supabase.table("reiatsu").update({"points": current + 1}).eq("user_id", str(user.id)).execute()
            else:
                supabase.table("reiatsu").insert({
                    "user_id": str(user.id),
                    "username": user.name,
                    "points": 1
                }).execute()

            await channel.send(f"{user.mention} a absorbé le Reiatsu et gagné **+1** point !")

        except asyncio.TimeoutError:
            await channel.send("Le Reiatsu s'est dissipé dans l'air... personne ne l'a absorbé.")

    @spawnreiatsu.before_invoke
    async def set_category(self, ctx):
        self.spawnreiatsu.category = "Reiatsu"

# 🔁 Chargement automatique
async def setup(bot):
    await bot.add_cog(SpawnReiatsuCommand(bot))
