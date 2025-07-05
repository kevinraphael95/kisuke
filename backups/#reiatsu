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
                "Réagis avec 📊 pour voir le top 10 des membres avec le plus de Reiatsu."
            ),
            color=user.color if user.color.value != 0 else discord.Color.blue()
        )
        embed.set_thumbnail(url=user.avatar.url)
        embed.set_footer(text=f"Demandé par {ctx.author.display_name}", icon_url=ctx.author.avatar.url)
        embed.timestamp = ctx.message.created_at

        message = await ctx.send(embed=embed)

        # Ajout automatique de la réaction 📊
        await message.add_reaction("📊")

        def check(reaction, user_react):
            return (
                user_react == ctx.author and
                reaction.message.id == message.id and
                str(reaction.emoji) == "📊"
            )

        try:
            reaction, user_react = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            await message.remove_reaction(reaction.emoji, user_react)

            # Récupérer top 10 Reiatsu
            top_data = supabase.table("reiatsu").select("user_id, points").order("points", desc=True).limit(10).execute()
            top_liste = []
            for i, row in enumerate(top_data.data):
                membre = ctx.guild.get_member(int(row["user_id"]))
                if membre:
                    top_liste.append(f"**{i+1}.** {membre.display_name} — `{row['points']} pts`")

            embed_top = discord.Embed(
                title="📊 Top 10 des Reiatsu",
                description="\n".join(top_liste) if top_liste else "Aucun score trouvé.",
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed_top)

        except Exception:
            pass

    def cog_load(self):
        self.reiatsu.category = "Reiatsu"

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
