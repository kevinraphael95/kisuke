import discord
from discord.ext import commands
from datetime import datetime
from dateutil import parser
import time
from supabase_client import supabase

class TempsReiatsuCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tempsreiatsu", aliases=["tpsrts"], help="Affiche le temps restant avant le prochain Reiatsu.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def tempsreiatsu(self, ctx):
        guild_id = str(ctx.guild.id)
        data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()

        if not data.data:
            await ctx.send("❌ Ce serveur n’a pas de salon Reiatsu configuré.")
            return

        conf = data.data[0]

        # 🟣 Si un Reiatsu est déjà en attente
        if conf.get("en_attente"):
            spawn_msg_id = conf.get("spawn_message_id")
            channel_id = conf.get("channel_id")

            if spawn_msg_id and channel_id:
                try:
                    channel = ctx.guild.get_channel(int(channel_id))
                    spawn_msg = await channel.fetch_message(int(spawn_msg_id))
                    await ctx.send("💠 Un Reiatsu est **déjà apparu** !", reference=spawn_msg)
                except:
                    await ctx.send("💠 Un Reiatsu est **déjà apparu**, mais le message est introuvable.")
            else:
                await ctx.send("💠 Un Reiatsu est **déjà apparu** et attend d’être absorbé.")
            return

        # ⏳ Sinon, calcule le temps restant
        delay = conf.get("delay_minutes", 1800)
        last_spawn_str = conf.get("last_spawn_at")

        if not last_spawn_str:
            await ctx.send("💠 Un Reiatsu peut apparaître **à tout moment** !")
            return

        last_spawn = parser.parse(last_spawn_str).timestamp()
        now = time.time()
        seconds_left = int((last_spawn + delay) - now)

        if seconds_left <= 0:
            await ctx.send("💠 Le Reiatsu peut apparaître **à tout moment** !")
        else:
            minutes = seconds_left // 60
            seconds = seconds_left % 60
            await ctx.send(f"⏳ Le prochain Reiatsu apparaîtra dans **{minutes}m {seconds}s**.")

    @tempsreiatsu.before_invoke
    async def set_category(self, ctx):
        self.tempsreiatsu.category = "Reiatsu"

# 📦 Chargement automatique
async def setup(bot):
    await bot.add_cog(TempsReiatsuCommand(bot))
