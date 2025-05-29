# ──────────────────────────────────────────────────────────────
# 📁 REIATSU - TEMPS RESTANT AVANT LE PROCHAIN SPAWN
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
import time
from datetime import datetime
from dateutil import parser
from discord.ext import commands
from supabase_client import supabase

# ──────────────────────────────────────────────────────────────
# 🔧 COG : TempsReiatsuCommand
# ──────────────────────────────────────────────────────────────
class TempsReiatsuCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────
    # ⏳ COMMANDE : tempsreiatsu
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="tempsreiatsu",
        aliases=["tpsrts"],
        help="Affiche le temps restant avant le prochain Reiatsu."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def tempsreiatsu(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)

        # 📦 Récupère les données de configuration
        res = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
        if not res.data:
            await ctx.send("❌ Ce serveur n’a pas encore de salon Reiatsu configuré (`!setreiatsu`).")
            return

        conf = res.data[0]

        # 💠 Un Reiatsu est déjà présent
        if conf.get("en_attente"):
            msg_id = conf.get("spawn_message_id")
            chan_id = conf.get("channel_id")

            if msg_id and chan_id:
                channel = ctx.guild.get_channel(int(chan_id))
                if channel:
                    try:
                        spawn_msg = await channel.fetch_message(int(msg_id))
                        await ctx.send("💠 Un Reiatsu est **déjà apparu** !", reference=spawn_msg)
                        return
                    except discord.NotFound:
                        pass

            await ctx.send("💠 Un Reiatsu est **déjà apparu**, mais son message est introuvable.")
            return

        # ⏳ Calcul du temps avant le prochain spawn
        delay = conf.get("delay_minutes", 1800)
        last_spawn_str = conf.get("last_spawn_at")

        if not last_spawn_str:
            await ctx.send("💠 Un Reiatsu peut apparaître **à tout moment** !")
            return

        last_spawn_ts = parser.parse(last_spawn_str).timestamp()
        now = time.time()
        remaining = int((last_spawn_ts + delay) - now)

        if remaining <= 0:
            await ctx.send("💠 Le Reiatsu peut apparaître **à tout moment** !")
        else:
            minutes = remaining // 60
            seconds = remaining % 60
            await ctx.send(f"⏳ Le prochain Reiatsu est attendu dans **{minutes}m {seconds}s**.")

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TempsReiatsuCommand(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
    print("✅ Cog chargé : TempsReiatsuCommand (Temps restant)")
