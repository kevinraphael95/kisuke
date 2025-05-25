import discord
from discord.ext import commands
from supabase_client import supabase

class ResetPersoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="resetperso", help="(Admin) Réinitialise tous les votes des personnages.")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def resetperso(self, ctx):
        try:
            supabase.table("perso_votes").delete().neq("nom", "").execute()
            await ctx.send("🗑️ Tous les votes ont été réinitialisés avec succès.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {e}")

# Chargement automatique
async def setup(bot):
    cog = ResetPersoCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
