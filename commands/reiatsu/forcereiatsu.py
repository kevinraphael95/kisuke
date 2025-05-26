import discord
from discord.ext import commands
from datetime import datetime
from supabase_client import supabase

class ForceSpawnCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="forcespawn", help="Force le spawn immédiat d’un Reiatsu (admin uniquement).")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.guild)
    async def forcespawn(self, ctx):
        guild_id = str(ctx.guild.id)
        config = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()

        if not config.data:
            await ctx.send("❌ Ce serveur n’a pas encore de configuration Reiatsu (`!setreiatsu`).")
            return

        now = datetime.utcnow().isoformat()

        supabase.table("reiatsu_config").update({
            "last_spawn_at": None,
            "delay_minutes": 1
        }).eq("guild_id", guild_id).execute()

        await ctx.send("💠 Spawn forcé déclenché. Un Reiatsu va apparaître dans la prochaine minute !")

# Chargement auto
async def setup(bot):
    cog = ForceSpawnCommand(bot)
    for command in cog.get_commands():
        command.category = "Admin"
    await bot.add_cog(cog)
