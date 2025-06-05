# ────────────────────────────────────────────────────────────────
# 🏆 TOP PERSOS - CLASSEMENT DES PERSONNAGES PRÉFÉRÉS
# ────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from supabase_client import supabase

class TopPersoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ────────────────────────────────────────────────
    # 🥇 COMMANDE : !topperso [limit]
    # Affiche les personnages les plus populaires selon les votes
    # ────────────────────────────────────────────────
    @commands.command(
        name="tupreftop",
        aliases=["toptupref"],
        help="📊 Affiche les personnages les plus aimés par les votes de la communauté."
    )
    async def topperso(self, ctx, limit: int = 10):
        # 🔒 Limite sécurisée
        if limit < 1 or limit > 50:
            await ctx.send("❌ Le nombre doit être **entre 1 et 50** pour éviter de surcharger le classement.")
            return

        # 📦 Récupération des données Supabase
        try:
            result = supabase.table("perso_votes") \
                             .select("nom", "votes") \
                             .order("votes", desc=True) \
                             .limit(limit) \
                             .execute()
        except Exception as e:
            await ctx.send(f"⚠️ Erreur lors de la récupération des données : `{e}`")
            return

        # 📉 Aucun vote
        if not result.data:
            await ctx.send("📉 Aucun vote n’a encore été enregistré. Sois le premier à voter !")
            return

        # 🎨 Embed stylisé
        embed = discord.Embed(
            title=f"🏆 Top {limit} des personnages les plus aimés",
            description="Voici le classement des **plus grands favoris** de la Soul Society 🌌",
            color=discord.Color.gold()
        )
        embed.set_footer(text="🔥 Basé sur les votes enregistrés par la communauté")

        # 🎖️ Classement dynamique
        medals = ["🥇", "🥈", "🥉"] + ["🔹"] * (limit - 3)
        for i, row in enumerate(result.data, start=1):
            emoji = medals[i - 1] if i <= len(medals) else "🔹"
            embed.add_field(
                name=f"{emoji} {i}. {row['nom']}",
                value=f"💖 **{row['votes']}** votes",
                inline=False
            )

        await ctx.send(embed=embed)

# ────────────────────────────────────────────────
# 🔌 Chargement automatique du cog
# ────────────────────────────────────────────────
async def setup(bot):
    cog = TopPersoCommand(bot)
    for command in cog.get_commands():
        command.category = "Bleach"
    await bot.add_cog(cog)
