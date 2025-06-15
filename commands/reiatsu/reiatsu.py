# ──────────────────────────────────────────────────────────────
# 📁 REIATSU - COMMANDES : SCORE, CLASSEMENT, TEMPS RESTANT
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
import time
from dateutil import parser
from discord.ext import commands
from supabase_client import supabase

# ──────────────────────────────────────────────────────────────
# 🔧 COG : ReiatsuCommand (score, classement, temps)
# ──────────────────────────────────────────────────────────────
class ReiatsuCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 💠 COMMANDE : !reiatsu
    @commands.command(
        name="reiatsu",
        aliases=["rts"],
        help="💠 Affiche le score de Reiatsu d’un membre (ou soi-même)."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def reiatsu(self, ctx: commands.Context, member: discord.Member = None):
        user = member or ctx.author
        user_id = str(user.id)

        data = supabase.table("reiatsu").select("points").eq("user_id", user_id).execute()
        points = data.data[0]["points"] if data.data else 0
        await ctx.send(f"💠 {user.mention} a **{points}** points de Reiatsu.")

    # 📊 COMMANDE : !reiatsuscore
    @commands.command(
        name="reiatsuscore",
        aliases=["rtsscore", "rtstop"],
        help="📊 Affiche le classement des membres avec le plus de points Reiatsu."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def reiatsuscore(self, ctx: commands.Context, limit: int = 10):
        if limit < 1 or limit > 50:
            await ctx.send("❌ Le nombre d’entrées doit être entre **1** et **50**.")
            return

        result = supabase.table("reiatsu") \
            .select("username", "points") \
            .order("points", desc=True) \
            .limit(limit).execute()

        if not result.data:
            await ctx.send("📉 Aucun Reiatsu n’a encore été collecté.")
            return

        embed = discord.Embed(
            title=f"🏆 Classement Reiatsu - Top {limit}",
            description="Voici les utilisateurs avec le plus de **points de Reiatsu**.",
            color=discord.Color.purple()
        )

        for i, row in enumerate(result.data, start=1):
            embed.add_field(
                name=f"**{i}.** {row['username']}",
                value=f"💠 {row['points']} points",
                inline=False
            )

        await ctx.send(embed=embed)

    # ⏳ COMMANDE : !reiatsutemps
    @commands.command(
        name="reiatsutemps",
        aliases=["rtstps", "rtst"],
        help="⏳ Affiche le temps restant avant le prochain Reiatsu."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def reiatsutemps(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        res = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
        if not res.data:
            await ctx.send("❌ Ce serveur n’a pas encore de salon Reiatsu configuré (`!setreiatsu`).")
            return

        conf = res.data[0]
        if conf.get("en_attente"):
            msg_id, chan_id = conf.get("spawn_message_id"), conf.get("channel_id")
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
            await ctx.send(f"⏳ Le prochain Reiatsu est attendu dans **{remaining // 60}m {remaining % 60}s**.")

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuCommand(bot)
    bot.add_cog(cog)

    # ✅ Attribution manuelle de la catégorie ici
    cog.reiatsu.category = "Reiatsu"
    cog.reiatsuscore.category = "Reiatsu"
    cog.reiatsutemps.category = "Reiatsu"

    print("✅ Cog chargé : ReiatsuCommand (catégorie = Reiatsu)")
