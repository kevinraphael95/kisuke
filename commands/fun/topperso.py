import discord
from discord.ext import commands
from supabase_client import supabase

class TopPersoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="topperso", help="Affiche les personnages les plus aimés par les votes.")
    async def topperso(self, ctx, limit: int = 10):
        if limit < 1 or limit > 50:
            await ctx.send("❌ Le nombre doit être entre 1 et 50.")
            return

        result = supabase.table("perso_votes").select("nom", "votes").order("votes", desc=True).limit(limit).execute()

        if not result.data:
            await ctx.send("📉 Aucun vote enregistré pour l'instant.")
            return

        embed = discord.Embed(
            title=f"🏆 Top {limit} des persos préférés",
            color=discord.Color.gold()
        )

        for i, row in enumerate(result.data, start=1):
            embed.add_field(name=f"{i}. {row['nom']}", value=f"💖 {row['votes']} votes", inline=False)

        await ctx.send(embed=embed)

# Chargement
async def setup(bot):
    cog = TopPersoCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
