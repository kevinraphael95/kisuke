# ──────────────────────────────────────────────────────────────
# 📁 REIATSU LEADERBOARD
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from supabase_client import supabase

# ──────────────────────────────────────────────────────────────
# 🔧 COG : Leaderboard
# ──────────────────────────────────────────────────────────────
class Leaderboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot  # 🔌 Référence au bot

    # ──────────────────────────────────────────────────────────
    # 📊 COMMANDE : !leaderboard [limit]
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="leaderboard",
        aliases=["toprts", "topreiatsu", "leadb"],
        help="📊 Affiche le classement des membres avec le plus de points Reiatsu."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🧊 Cooldown : 3s/user
    async def leaderboard(self, ctx: commands.Context, limit: int = 10):
        # 🔎 Validation des bornes
        if limit < 1 or limit > 50:
            await ctx.send("❌ Le nombre d’entrées doit être entre **1** et **50**.")
            return

        # 🗃️ Requête vers Supabase pour récupérer les données triées
        result = supabase.table("reiatsu") \
                         .select("username", "points") \
                         .order("points", desc=True) \
                         .limit(limit) \
                         .execute()

        # 📉 Aucun résultat
        if not result.data:
            await ctx.send("📉 Aucun Reiatsu n’a encore été collecté.")
            return

        # 🖼️ Création de l'embed classement
        embed = discord.Embed(
            title=f"🏆 Classement Reiatsu - Top {limit}",
            description="Voici les utilisateurs avec le plus de **points de Reiatsu**.",
            color=discord.Color.purple()
        )

        for i, row in enumerate(result.data, start=1):
            username = row["username"]
            points = row["points"]
            embed.add_field(
                name=f"**{i}.** {username}",
                value=f"💠 {points} points",
                inline=False
            )

        await ctx.send(embed=embed)

    # 🏷️ Attribution de la catégorie
    def cog_load(self):
        self.leaderboard.category = "Reiatsu"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(Leaderboard(bot))
    print("✅ Cog chargé : Leaderboard (catégorie = Reiatsu)")
