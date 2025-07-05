# ──────────────────────────────────────────────────────────────
# 📁 REIATSU - AFFICHAGE DE SCORE + INTERACTIONS
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from supabase_client import supabase
from datetime import datetime
import time
from dateutil import parser

# ──────────────────────────────────────────────────────────────
# COG PRINCIPAL
# ──────────────────────────────────────────────────────────────
class ReiatsuCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────────
    # COMMANDE PRINCIPALE
    # ──────────────────────────────────────────────────────────────
    @commands.command(
        name="reiatsu",
        aliases=["rts"],
        help="💠 Affiche le score de Reiatsu d’un membre (ou soi-même)."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def reiatsu(self, ctx: commands.Context, member: discord.Member = None):
        user = member or ctx.author
        user_id = str(user.id)
        guild_id = str(ctx.guild.id)

        # Récupération des points
        data = supabase.table("reiatsu") \
                       .select("points") \
                       .eq("user_id", user_id) \
                       .execute()
        points = data.data[0]["points"] if data.data else 0

        # Embed principal
        embed = discord.Embed(
            title="💠 Score de Reiatsu",
            description=f"{user.mention} a **{points}** points de Reiatsu.",
            color=user.color if user.color.value != 0 else discord.Color.blue()
        )
        embed.set_thumbnail(url=user.avatar.url)
        embed.set_footer(text=f"Demandé par {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        embed.timestamp = ctx.message.created_at
        msg = await ctx.send(embed=embed)

        # Ajout de la réaction 📊 pour afficher le top
        emoji = "📊"
        await msg.add_reaction(emoji)

        # Affichage direct des informations secondaires
        await self.send_reiatsu_channel(ctx)
# ──────────────────────────────────────────────────────────────
# 📁 REIATSU - AFFICHAGE DE SCORE + INTERACTIONS
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from supabase_client import supabase
from datetime import datetime
import time
from dateutil import parser

# ──────────────────────────────────────────────────────────────
# COG PRINCIPAL
# ──────────────────────────────────────────────────────────────
class ReiatsuCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────────
    # COMMANDE PRINCIPALE
    # ──────────────────────────────────────────────────────────────
    @commands.command(
        name="reiatsu",
        aliases=["rts"],
        help="💠 Affiche le score de Reiatsu d’un membre (ou soi-même)."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def reiatsu(self, ctx: commands.Context, member: discord.Member = None):
        user = member or ctx.author
        user_id = str(user.id)
        guild_id = str(ctx.guild.id)

        # Récupération des points
        data = supabase.table("reiatsu") \
                       .select("points") \
                       .eq("user_id", user_id) \
                       .execute()
        points = data.data[0]["points"] if data.data else 0

        # Embed principal
        embed = discord.Embed(
            title="💠 Score de Reiatsu",
            description=f"{user.mention} a **{points}** points de Reiatsu.",
            color=user.color if user.color.value != 0 else discord.Color.blue()
        )
        embed.set_thumbnail(url=user.avatar.url)
        embed.set_footer(text=f"Demandé par {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        embed.timestamp = ctx.message.created_at
        msg = await ctx.send(embed=embed)

        # Ajout de la réaction 📊 pour afficher le top
        emoji = "📊"
        await msg.add_reaction(emoji)

        # Affichage direct des informations secondaires
        await self.send_reiatsu_channel(ctx)
        await self.send_reiatsu_timer(ctx)

        # Gestion de la réaction pour afficher le top
        def check(reaction, user_react):
            return (
                reaction.message.id == msg.id
                and user_react.id == ctx.author.id
                and str(reaction.emoji) == emoji
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            await msg.remove_reaction(reaction.emoji, ctx.author)
            await self.send_reiatsu_top(ctx)
        except Exception:
            pass  # Timeout ou autre, on ignore silencieusement

    # ──────────────────────────────────────────────────────────────
    # MÉTHODES SECONDAIRES
    # ──────────────────────────────────────────────────────────────

    # 📍 Affiche le salon Reiatsu configuré
    async def send_reiatsu_channel(self, ctx):
        guild_id = str(ctx.guild.id)
        data = supabase.table("reiatsu_config").select("channel_id").eq("guild_id", guild_id).execute()
        if data.data:
            channel_id = int(data.data[0]["channel_id"])
            channel = self.bot.get_channel(channel_id)
            if channel:
                await ctx.send(f"💠 Le Reiatsu apparaît sur le salon : {channel.mention}")
            else:
                await ctx.send("⚠️ Le salon configuré n'existe plus ou n'est pas accessible.")
        else:
            await ctx.send("❌ Aucun salon Reiatsu n’a encore été configuré avec `!setreiatsu`.")

    # ⏳ Affiche le temps restant avant le prochain spawn
    async def send_reiatsu_timer(self, ctx):
        guild_id = str(ctx.guild.id)
        res = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()

        if not res.data:
            await ctx.send("❌ Ce serveur n’a pas encore de salon Reiatsu configuré (`!setreiatsu`).")
            return

        conf = res.data[0]

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

        delay = conf.get("delay_minutes", 1800)
        last_spawn_str = conf.get("last_spawn_at")

        if not last_spawn_str:
            await ctx.send("💠 Le Reiatsu va apparaître dans : **à tout moment** !")
            return

        last_spawn_ts = parser.parse(last_spawn_str).timestamp()
        now = time.time()
        remaining = int((last_spawn_ts + delay) - now)

        if remaining <= 0:
            await ctx.send("💠 Le Reiatsu va apparaître dans : **à tout moment** !")
        else:
            minutes = remaining // 60
            seconds = remaining % 60
            await ctx.send(f"💠 Le Reiatsu va apparaître dans : **{minutes}m {seconds}s**.")

    # 🏆 Affiche le classement des 10 meilleurs joueurs
    async def send_reiatsu_top(self, ctx):
        result = supabase.table("reiatsu").select("username", "points").order("points", desc=True).limit(10).execute()
        if not result.data:
            await ctx.send("📉 Aucun Reiatsu n’a encore été collecté.")
            return

        embed = discord.Embed(
            title="🏆 Classement Reiatsu - Top 10",
            description="Voici les utilisateurs avec le plus de **points de Reiatsu**.",
            color=discord.Color.purple()
        )

        for i, row in enumerate(result.data, start=1):
            embed.add_field(name=f"**{i}.** {row['username']}", value=f"💠 {row['points']} points", inline=False)

        await ctx.send(embed=embed)

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ReiatsuCommand(bot))
    print("✅ Cog chargé : ReiatsuCommand (catégorie = Reiatsu)")

        await self.send_reiatsu_timer(ctx)

        # Gestion de la réaction pour afficher le top
        def check(reaction, user_react):
            return (
                reaction.message.id == msg.id
                and user_react.id == ctx.author.id
                and str(reaction.emoji) == emoji
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            await msg.remove_reaction(reaction.emoji, ctx.author)
            await self.send_reiatsu_top(ctx)
        except Exception:
            pass  # Timeout ou autre, on ignore silencieusement

    # ──────────────────────────────────────────────────────────────
    # MÉTHODES SECONDAIRES
    # ──────────────────────────────────────────────────────────────

    # 📍 Affiche le salon Reiatsu configuré
    async def send_reiatsu_channel(self, ctx):
        guild_id = str(ctx.guild.id)
        data = supabase.table("reiatsu_config").select("channel_id").eq("guild_id", guild_id).execute()
        if data.data:
            channel_id = int(data.data[0]["channel_id"])
            channel = self.bot.get_channel(channel_id)
            if channel:
                await ctx.send(f"💠 Le Reiatsu apparaît sur le salon : {channel.mention}")
            else:
                await ctx.send("⚠️ Le salon configuré n'existe plus ou n'est pas accessible.")
        else:
            await ctx.send("❌ Aucun salon Reiatsu n’a encore été configuré avec `!setreiatsu`.")

    # ⏳ Affiche le temps restant avant le prochain spawn
    async def send_reiatsu_timer(self, ctx):
        guild_id = str(ctx.guild.id)
        res = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
        if not res.data:
            await ctx.send("❌ Ce serveur n’a pas encore de salon Reiatsu configuré (`!setreiatsu`).")
            return

        conf = res.data[0]
        if conf.get("en_attente"):
fiche le classement des 10 meilleurs joueurs
    async def send_reiatsu_top(self, ctx):
        result = supabase.table("reiatsu").select("username", "points").order("points", desc=True).limit(10).execute()
        if not result.data:
            await ctx.send("📉 Aucun Reiatsu n’a encore été collecté.")
            return

        embed = discord.Embed(
            title="🏆 Classement Reiatsu - Top 10",
            description="Voici les utilisateurs avec le plus de **points de Reiatsu**.",
            color=discord.Color.purple()
        )

        for i, row in enumerate(result.data, start=1):
            embed.add_field(name=f"**{i}.** {row['username']}", value=f"💠 {row['points']} points", inline=False)

        await ctx.send(embed=embed)

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ReiatsuCommand(bot))
    print("✅ Cog chargé : ReiatsuCommand (catégorie = Reiatsu)")
