# 📁 commands/reiatsu/spawner.py

import asyncio
import random
import time
from datetime import datetime
from dateutil import parser

import discord
from discord.ext import commands, tasks

from supabase_client import supabase

class ReiatsuSpawner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spawn_loop.add_exception_type(asyncio.CancelledError)
        self.spawn_loop.start()

    def cog_unload(self):
        self.spawn_loop.cancel()

    @tasks.loop(seconds=60)
    async def spawn_loop(self):
        await self.bot.wait_until_ready()

        if not getattr(self.bot, "is_main_instance", False):
            return

        now = int(time.time())

        configs = supabase.table("reiatsu_config") \
            .select("guild_id", "channel_id", "last_spawn_at", "delay_minutes") \
            .execute()

        for conf in configs.data:
            guild_id = conf["guild_id"]
            channel_id = conf.get("channel_id")
            if not channel_id:
                continue

            last_spawn_str = conf.get("last_spawn_at")
            delay = conf.get("delay_minutes") or 1800

            if not last_spawn_str:
                should_spawn = True
            else:
                last_spawn = parser.parse(last_spawn_str).timestamp()
                should_spawn = now - int(last_spawn) >= int(delay)

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
            await message.add_reaction("\U0001f4a0")

            def check(reaction, user):
                return (
                    reaction.message.id == message.id and
                    str(reaction.emoji) == "💠" and
                    not user.bot
                )

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=10800.0, check=check)

                data = supabase.table("reiatsu").select("id", "points").eq("user_id", str(user.id)).execute()
                if data.data:
                    current = data.data[0]["points"]
                    supabase.table("reiatsu").update({"points": current + 1}).eq("user_id", str(user.id)).execute()
                else:
                    supabase.table("reiatsu").insert({
                        "user_id": str(user.id),
                        "username": str(user.name),
                        "points": 1
                    }).execute()

                await channel.send(f"{user.mention} a absorbé le Reiatsu et gagné **+1** point !")

            except asyncio.TimeoutError:
                await channel.send("Le Reiatsu s'est dissipé dans l'air... personne ne l'a absorbé.")

            new_delay = random.randint(1800, 5400)
            supabase.table("reiatsu_config").update({
                "last_spawn_at": datetime.utcnow().isoformat(),
                "delay_minutes": new_delay
            }).eq("guild_id", guild_id).execute()

async def setup(bot):
    await bot.add_cog(ReiatsuSpawner(bot))
