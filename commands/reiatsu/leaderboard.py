import discord
from discord.ext import commands
from supabase_client import supabase

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="leaderboard", aliases=["toprts", "topreiatsu", "leadb"], help="Affiche le classement Reiatsu.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown 3s par utilisateur
    async def leaderboard(self, ctx, limit: int = 10):
        """Affiche le classement des membres avec le plus de points de Reiatsu."""
        if limit < 1 or limit > 50:
            await ctx.send("❌ Le nombre d’entrées doit être entre 1 et 50.")
            return

        result = supabase.table("reiatsu").select("username", "points").order("points", desc=True).limit(limit).execute()

        if not result.data:
            await ctx.send("📉 Aucun Reiatsu n’a encore été collecté.")
            return

        embed = discord.Embed(
            title=f"🏆 Classement Reiatsu - Top {limit}",
            description="Voici les utilisateurs avec le plus de points de Reiatsu.",
            color=discord.Color.purple()
        )

        for i, row in enumerate(result.data, start=1):
            username = row["username"]
            points = row["points"]
            embed.add_field(name=f"{i}. {username}", value=f"💠 {points} points", inline=False)

        await ctx.send(embed=embed)

    @leaderboard.before_invoke
    async def before_leaderboard(self, ctx):
        self.leaderboard.category = "Reiatsu"

# Chargement auto
async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
