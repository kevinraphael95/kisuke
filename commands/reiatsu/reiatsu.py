# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu.py — Commande interactive !reiatsu
# Objectif : Afficher le score de reiatsu, le salon de spawn, le temps avant prochain spawn,
#           et permettre d’afficher le top 10 via réaction.
# Catégorie : Reiatsu
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuCommand(commands.Cog):
    """
    Commande !reiatsu — Affiche le score de reiatsu d’un membre (ou soi-même),
    le salon où le reiatsu apparaît, le temps avant le prochain spawn,
    et affiche le top 10 via réaction.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="reiatsu",
        aliases=["rts"],
        help="Affiche le score de Reiatsu d’un membre, le salon, le temps restant et le top 10."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def reiatsu(self, ctx: commands.Context, member: discord.Member = None):
        user = member or ctx.author
        user_id = str(user.id)

        # Récupération des points de Reiatsu de l'utilisateur
        data = supabase.table("reiatsu").select("points").eq("user_id", user_id).execute()
        points = data.data[0]["points"] if data.data else 0

        # Recherche du salon Reiatsu (à adapter)
        salon_reiatsu = discord.utils.get(ctx.guild.text_channels, name="reiatsu-spawn")

        # Récupération du dernier spawn et délai (exemple de table "reiatsu_spawn")
        spawn_data = supabase.table("reiatsu_spawn").select("last_spawn_at, delay_minutes").limit(1).execute()
        if spawn_data.data:
            last_spawn_str = spawn_data.data[0].get("last_spawn_at")
            delay = spawn_data.data[0].get("delay_minutes", 10)
            if last_spawn_str:
                last_spawn = datetime.fromisoformat(last_spawn_str)
                prochain_spawn = last_spawn + timedelta(minutes=delay)
                now = datetime.utcnow()
                reste = max(prochain_spawn - now, timedelta(seconds=0))
                minutes_restantes = reste.seconds // 60
                secondes_restantes = reste.seconds % 60
                temps_restant = f"{minutes_restantes}m {secondes_restantes}s"
            else:
                temps_restant = "Inconnu"
        else:
            temps_restant = "Inconnu"

        embed = discord.Embed(
            title="💠 Score de Reiatsu",
            description=(
                f"{user.mention} a **{points}** points de Reiatsu.\n\n"
                f"ℹ️ Le Reiatsu apparaît dans le salon {salon_reiatsu.mention if salon_reiatsu else '*non trouvé*'}.\n"
                f"🕒 Le prochain Reiatsu apparaîtra dans **{temps_restant}**.\n\n"
# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu.py — Commande interactive !reiatsu
# Objectif : Affiche le score Reiatsu d’un membre, le salon de spawn et le temps restant
# Catégorie : Reiatsu
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from dateutil import parser
import time
from supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuCommand(commands.Cog):
    """
    Commande !reiatsu — Affiche ton score de Reiatsu, le salon et le temps avant le prochain spawn.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="reiatsu",
        aliases=["rts"],
        help="💠 Affiche le score de Reiatsu d’un membre (ou soi-même).",
        description="Affiche le score, le salon de spawn et le temps restant avant le prochain Reiatsu."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def reiatsu(self, ctx: commands.Context, member: discord.Member = None):
        user = member or ctx.author
        user_id = str(user.id)
        guild_id = str(ctx.guild.id)

        # 📦 Requête : Score utilisateur
        score_data = supabase.table("reiatsu") \
            .select("points") \
            .eq("user_id", user_id) \
            .execute()
        points = score_data.data[0]["points"] if score_data.data else 0

        # 📦 Requête : Configuration serveur
        config_data = supabase.table("reiatsu_config") \
            .select("*") \
            .eq("guild_id", guild_id) \
            .execute()
        config = config_data.data[0] if config_data.data else None

        # 🛠️ Préparation des infos config
        salon_text = "❌ Aucun salon configuré"
        temps_text = "⚠️ Inconnu"
        if config:
            # Salon
            salon = ctx.guild.get_channel(int(config["channel_id"])) if config.get("channel_id") else None
            salon_text = salon.mention if salon else "⚠️ Salon introuvable"

            # Temps
            if config.get("en_attente"):
                temps_text = "💠 Un Reiatsu est **déjà apparu** !"
            else:
                last_spawn = config.get("last_spawn_at")
                delay = config.get("delay_minutes", 1800)
                if last_spawn:
                    last_ts = parser.parse(last_spawn).timestamp()
                    now = time.time()
                    remaining = int((last_ts + delay) - now)
                    if remaining <= 0:
                        temps_text = "💠 Un Reiatsu peut apparaître **à tout moment** !"
                    else:
                        minutes, seconds = divmod(remaining, 60)
                        temps_text = f"⏳ Prochain dans **{minutes}m {seconds}s**"
                else:
                    temps_text = "💠 Un Reiatsu peut apparaître **à tout moment** !"

        # 📋 Création de l'embed
        embed = discord.Embed(
            title="💠 Score de Reiatsu",
            description=f"**{user.display_name}** a actuellement :\n**{points}** points de Reiatsu\n\n"
                        f"__**Infos**__\n"
                        f"📍 Le Reiatsu apparaît sur le salon : {salon_text}\n"
                        f"⏳ Le Reiatsu va apparaître dans : {temps_text}",
            color=discord.Color.purple()
        )
        embed.set_footer(text="Réagis avec 📊 pour voir le classement.")

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("📊")

        # 🔁 Écoute des réactions (classement)
        def check(reaction, user_check):
            return (
                reaction.message.id == msg.id and
                str(reaction.emoji) == "📊" and
                user_check == ctx.author
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", check=check, timeout=30)
            await self.show_leaderboard(ctx, original_message=msg)
        except Exception:
            pass  # Timeout ou erreur : on ne fait rien

    async def show_leaderboard(self, ctx, original_message=None):
        # 📦 Requête : Classement
        leaderboard = supabase.table("reiatsu") \
            .select("user_id, points") \
            .order("points", desc=True) \
            .limit(10) \
            .execute().data

        embed = discord.Embed(
            title="📊 Top 10 des utilisateurs Reiatsu",
            color=discord.Color.gold()
        )

        for i, entry in enumerate(leaderboard, start=1):
            member = ctx.guild.get_member(int(entry["user_id"]))
            name = member.display_name if member else f"<Inconnu {entry['user_id']}>"
            embed.add_field(name=f"#{i} — {name}", value=f"**{entry['points']}** points", inline=False)

        await ctx.send(embed=embed, reference=original_message)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuCommand(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
    print("✅ Cog chargé : ReiatsuCommand (catégorie = Reiatsu)")

