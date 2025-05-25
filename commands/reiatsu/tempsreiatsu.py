import discord
import time
from discord.ext import commands
from dateutil import parser
from supabase_client import supabase

class TempsReiatsuCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="tempsreiatsu",
        aliases=["tpsrts"],
        help="Affiche le temps restant avant le prochain spawn automatique de Reiatsu."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown 3s
    async def tempsreiatsu(self, ctx):
        guild_id = str(ctx.guild.id)
        config = supabase.table("reiatsu_config") \
            .select("last_spawn_at", "delay_minutes") \
            .eq("guild_id", guild_id).execute()

        if not config.data:
            await ctx.send("❌ Ce serveur n'a pas de config Reiatsu (`!setreiatsu`).")
            return

        conf = config.data[0]
        last_spawn_str = conf.get("last_spawn_at")
        last = parser.parse(last_spawn_str).timestamp() if last_spawn_str else 0
        delay = conf.get("delay_minutes") or 1800

        restant = max(0, (int(last) + int(delay)) - int(time.time()))
        if restant == 0:
            await ctx.send("💠 Le Reiatsu peut apparaître à tout moment !")
        else:
            minutes = restant // 60
            secondes = restant % 60
            await ctx.send(f"⏳ Prochain spawn automatique dans **{minutes}m {secondes}s**.")

# Chargement automatique du cog + catégorie
async def setup(bot):
    cog = TempsReiatsuCommand(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
