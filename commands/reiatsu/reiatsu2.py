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
from datetime import datetime, timedelta
import time
from supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Reiatsu2Command(commands.Cog):
    """
    Commande !reiatsu — Affiche ton score de Reiatsu, le salon et le temps avant le prochain spawn.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="reiatsu2",
        aliases=["rts2"],
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

        # 📦 Requête : Dernier vol
        steal_data = supabase.table("reiatsu") \
            .select("last_steal_attempt") \
            .eq("user_id", user_id) \
            .execute()
        cooldown_text = "✅ Disponible"
        if steal_data.data and steal_data.data[0].get("last_steal_attempt"):
            last_steal = parser.parse(steal_data.data[0]["last_steal_attempt"])
            next_steal = last_steal + timedelta(hours=24)
            now = datetime.utcnow()
            if now < next_steal:
                restant = next_steal - now
                h, m = divmod(restant.seconds // 60, 60)
                cooldown_text = f"⏳ {restant.days}j {h}h{m}m"

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
                    now_ts = time.time()
                    remaining = int((last_ts + delay) - now_ts)
                    if remaining <= 0:
                        temps_text = "💠 Un Reiatsu peut apparaître **à tout moment** !"
                    else:
                        minutes, seconds = divmod(remaining, 60)
                        temps_text = f"**{minutes}m {seconds}s**"
                else:
                    temps_text = "💠 Un Reiatsu peut apparaître **à tout moment** !"

        # 📋 Création de l'embed
        embed = discord.Embed(
            title="__**💠 Score de Reiatsu**__",
            description=(
                f"**{user.display_name}** a actuellement :\n"
                f"**{points}** points de Reiatsu\n\n"
                f"__**Infos**__\n"
                f"📍 Le Reiatsu apparaît sur le salon : *_n"
                "{salon_text}\n"
                f"⏳ Le Reiatsu va apparaître dans : *_n"
                "{temps_text}\n"
                f"🕵️ Temps avant de pouvoir tenter un vol : _n"
                "{cooldown_text}"
            ),
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
        leaderboard_resp = supabase.table("reiatsu") \
            .select("user_id, points") \
            .order("points", desc=True) \
            .limit(10) \
            .execute()

        leaderboard = leaderboard_resp.data if leaderboard_resp.data else []

        # 📄 Génération du bloc texte
        top_texte = ""
        for i, entry in enumerate(leaderboard, start=1):
            member = ctx.guild.get_member(int(entry["user_id"]))
            name = member.display_name if member else f"<Inconnu {entry['user_id']}>"
            points = entry["points"]
            top_texte += f"**#{i}** — {name} : {points} pts\n"

        # 🖼️ Embed final
        embed = discord.Embed(
            title="📊 Top 10 des utilisateurs avec le plus de Reiatsu",
            description=top_texte,
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed, reference=original_message)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Reiatsu2Command(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
    print("✅ Cog chargé : Reiatsu2Command (catégorie = Reiatsu)")
