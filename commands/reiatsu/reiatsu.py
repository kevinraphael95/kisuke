# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu.py — Commande informative !reiatsu
# Objectif : Affiche le score de Reiatsu d’un utilisateur
# Catégorie : VAACT
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from dateutil import parser
from supabase_client import supabase  # ⚠️ Remplace par ton instance Supabase

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Reiatsu(commands.Cog):
    """
    Commande !reiatsu — Affiche le score de Reiatsu et informations liées
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="reiatsu",
        aliases=["rts", "spirit"],
        help="Affiche ton niveau de Reiatsu ou celui d’un autre membre.",
        description="Renvoie un embed avec les points de Reiatsu, le salon de spawn et le temps avant le prochain spawn."
    )
    async def reiatsu(self, ctx: commands.Context, membre: discord.Member = None):
        """Commande principale pour afficher les informations de Reiatsu."""
        try:
            user = membre or ctx.author
            user_id = str(user.id)

            # 📦 Requête : Score utilisateur
            score_data = supabase.table("reiatsu") \
                .select("points, last_steal_attempt") \
                .eq("user_id", user_id) \
                .execute()

            points = score_data.data[0]["points"] if score_data.data else 0
            last_steal_str = score_data.data[0].get("last_steal_attempt") if score_data.data else None

            # 📍 Récupération du salon de spawn (config globale)
            config_data = supabase.table("reiatsu_config") \
                .select("channel_id, last_spawn_at, delay_minutes") \
                .single() \
                .execute()

            config = config_data.data or {}
            channel_id = config.get("channel_id")
            channel = self.bot.get_channel(int(channel_id)) if channel_id else None

            # ⏳ Temps avant prochain spawn
            last_spawn = parser.parse(config.get("last_spawn_at")) if config.get("last_spawn_at") else None
            delay_minutes = config.get("delay_minutes", 60)
            time_left = "Inconnu"

            if last_spawn:
                now = datetime.utcnow()
                next_spawn = last_spawn + timedelta(minutes=delay_minutes)
                if now < next_spawn:
                    delta = next_spawn - now
                    minutes, seconds = divmod(int(delta.total_seconds()), 60)
                    time_left = f"{minutes}m {seconds}s"
                else:
                    time_left = "Imminent !"

            # 🪽 Cooldown du vol
            vol_text = "🪽 Tu peux **voler du Reiatsu** dès maintenant !"
            if last_steal_str:
                last_steal = parser.parse(last_steal_str)
                cooldown = last_steal + timedelta(hours=24)
                now = datetime.utcnow()
                if now < cooldown:
                    delta = cooldown - now
                    d, rem = divmod(delta.seconds, 3600)
                    h = d
                    m = (rem // 60)
                    vol_text = f"🪽 Tu pourras voler du Reiatsu dans **{delta.days}j {h}h{m}m**."

            # 📤 Embed d'affichage
            embed = discord.Embed(
                title=f"💠 Reiatsu de {user.display_name}",
                color=discord.Color.purple()
            )
            embed.add_field(name="🔢 Points", value=f"**{points}**", inline=False)
            if channel:
                embed.add_field(name="📍 Salon de spawn", value=channel.mention, inline=False)
            embed.add_field(name="⏳ Temps restant", value=f"Prochain dans **{time_left}**", inline=False)
            embed.add_field(name="🪽 Vol de Reiatsu", value=vol_text, inline=False)

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"[ERREUR reiatsu] {e}")
            await ctx.send("❌ Une erreur est survenue lors de la récupération des données.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Reiatsu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
