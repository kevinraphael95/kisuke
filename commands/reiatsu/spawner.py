import discord
import random
import time
from datetime import datetime
from dateutil import parser

from discord.ext import commands, tasks
from supabase_client import supabase

class ReiatsuSpawner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(seconds=60)
    async def spawn_loop(self):
        await self.bot.wait_until_ready()
        if not getattr(self.bot, "is_main_instance", True):
            return

        now = int(time.time())
        configs = supabase.table("reiatsu_config").select("*").execute()

        for conf in configs.data:
            guild_id = conf["guild_id"]
            channel_id = conf.get("channel_id")
            en_attente = conf.get("en_attente", False)
            delay = conf.get("delay_minutes") or 1800

            if not channel_id or en_attente:
                continue

            last_spawn_str = conf.get("last_spawn_at")
            should_spawn = not last_spawn_str or (now - int(parser.parse(last_spawn_str).timestamp()) >= delay)

            if not should_spawn:
                continue

            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                continue

            embed = discord.Embed(
                title="💠 Un Reiatsu sauvage apparaît !",
                description="Cliquez sur la réaction 💠 pour l'absorber.",
                color=discord.Color.purple()
            )
            message = await channel.send(embed=embed)
            await message.add_reaction("💠")

            # Sauvegarde
            supabase.table("reiatsu_config").update({
                "en_attente": True,
                "last_spawn_at": datetime.utcnow().isoformat(),
                "spawn_message_id": str(message.id)
            }).eq("guild_id", guild_id).execute()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) != "💠" or payload.user_id == self.bot.user.id:
            return

        guild_id = str(payload.guild_id)
        conf_data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
        if not conf_data.data:
            return

        conf = conf_data.data[0]
        if not conf.get("en_attente") or str(payload.message_id) != conf.get("spawn_message_id"):
            return

        guild = self.bot.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        user = guild.get_member(payload.user_id)
        if not channel or not user:
            return

        # Ajoute le point
        user_id = str(user.id)
        reiatsu = supabase.table("reiatsu").select("points").eq("user_id", user_id).execute()
        if reiatsu.data:
            points = reiatsu.data[0]["points"] + 1
            supabase.table("reiatsu").update({"points": points}).eq("user_id", user_id).execute()
        else:
            supabase.table("reiatsu").insert({
                "user_id": user_id,
                "username": user.name,
                "points": 1
            }).execute()

        await channel.send(f"{user.mention} a absorbé le Reiatsu et gagné **+1** point !")

        # Réinitialise l’état
        new_delay = random.randint(1800, 5400)
        supabase.table("reiatsu_config").update({
            "en_attente": False,
            "spawn_message_id": None,
            "delay_minutes": new_delay
        }).eq("guild_id", guild_id).execute()

# Chargement
async def setup(bot):
    await bot.add_cog(ReiatsuSpawner(bot))
