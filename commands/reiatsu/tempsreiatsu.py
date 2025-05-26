import discord
from discord.ext import commands
from supabase_client import supabase
from dateutil import parser
import time

class TempsReiatsuCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tempsreiatsu", aliases=["tpsrts"], help="Affiche le temps restant avant le prochain spawn de Reiatsu.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def tempsreiatsu(self, ctx):
        guild_id = str(ctx.guild.id)

        # 🔎 Récupération de la config serveur
        config = supabase.table("reiatsu_config") \
            .select("last_spawn_at", "delay_minutes", "en_attente") \
            .eq("guild_id", guild_id).execute()

        if not config.data:
            await ctx.send("❌ Ce serveur n'a pas de configuration Reiatsu. Utilise `!setreiatsu` d’abord.")
            return

        conf = config.data[0]
        last_spawn_str = conf.get("last_spawn_at")
        delay = conf.get("delay_minutes") or 1800
        en_attente = conf.get("en_attente", False)

        now_ts = int(time.time())
        last_spawn_ts = parser.parse(last_spawn_str).timestamp() if last_spawn_str else 0
        time_remaining = max(0, (last_spawn_ts + delay) - now_ts)

        if en_attente:
            await ctx.send("💠 Un Reiatsu est **déjà apparu** et attend d’être absorbé.")
        elif time_remaining <= 0:
            await ctx.send("🔄 Le Reiatsu peut **apparaître à tout moment**.")
        else:
            minutes = time_remaining // 60
            seconds = time_remaining % 60
            await ctx.send(f"⏳ Prochain spawn possible dans **{minutes}m {seconds}s**.")

# 📦 Chargement automatique
async def setup(bot):
    cog = TempsReiatsuCommand(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
