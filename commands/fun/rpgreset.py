import discord
from discord.ext import commands
from supabase_client import supabase

class RPGReset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="rpgreset", help="Réinitialise ta progression RPG, ou celle d’un autre joueur (admin uniquement).")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rpgreset(self, ctx, membre: discord.Member = None):
        cible = membre or ctx.author

        # Si c'est quelqu'un d'autre et que l'auteur n'est pas admin, on refuse
        if cible != ctx.author and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Tu n’as pas la permission de réinitialiser la progression des autres.")
            return

        supabase.table("rpg_save").delete().eq("user_id", str(cible.id)).execute()

        if cible == ctx.author:
            await ctx.send("🗑️ Ta progression a été réinitialisée.")
        else:
            await ctx.send(f"🗑️ La progression RPG de {cible.mention} a été réinitialisée par un administrateur.")

# Chargement automatique
async def setup(bot):
    cog = RPGReset(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
