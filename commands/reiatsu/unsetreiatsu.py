import discord
from discord.ext import commands
from supabase_client import supabase

class UnsetReiatsuCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="unsetreiatsu",
        aliases=["unsetrts"],
        help="Supprime le salon configuré pour le spawn de Reiatsu. (Admin uniquement)"
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown 3s
    @commands.has_permissions(administrator=True)
    async def unsetreiatsu(self, ctx):
        guild_id = str(ctx.guild.id)

        data = supabase.table("reiatsu_config").select("id").eq("guild_id", guild_id).execute()
        if data.data:
            supabase.table("reiatsu_config").delete().eq("guild_id", guild_id).execute()
            await ctx.send("🗑️ Le salon Reiatsu a été supprimé de la configuration.")
        else:
            await ctx.send("❌ Aucun salon Reiatsu n'était configuré pour ce serveur.")


# ✅ Chargement automatique avec catégorie définie dès le setup
async def setup(bot):
    cog = unsetreiatsu(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)

# Chargement automatique du module
async def setup(bot):
    await bot.add_cog(UnsetReiatsuCommand(bot))
