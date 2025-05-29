# ──────────────────────────────────────────────────────────────
# 📁 REIATSU ─ Changer les points d’un membre
# ──────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
from supabase_client import supabase

# ──────────────────────────────────────────────────────────────
# 🔧 COG : SetReiatsuPoints
# ──────────────────────────────────────────────────────────────
class SetReiatsuPoints(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # 🔌 Stockage de l’instance du bot

    # ──────────────────────────────────────────────────────────
    # 🛠️ COMMANDE : !changereiatsu @membre <points>
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="changereiatsu",
        aliases=["changerts"],
        help="(Admin) Modifie le score Reiatsu d’un membre."
    )
    @commands.has_permissions(administrator=True)  # 🔐 Réservé aux admins
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)  # 🧊 Cooldown de 5 secondes
    async def changereiatsu(self, ctx, member: discord.Member, points: int):
        # 🔎 Vérifie que le score est positif
        if points < 0:
            await ctx.send("❌ Le score Reiatsu doit être un nombre **positif**.")
            return

        # 📊 Récupère les données utilisateur
        user_id = str(member.id)
        username = member.display_name

        try:
            # 📡 Requête à Supabase
            data = supabase.table("reiatsu").select("id").eq("user_id", user_id).execute()

            if data.data:
                # 🔄 Mise à jour des points existants
                supabase.table("reiatsu").update({
                    "points": points
                }).eq("user_id", user_id).execute()
                status = "🔄 Score mis à jour"
            else:
                # 🆕 Création d’un nouveau score
                supabase.table("reiatsu").insert({
                    "user_id": user_id,
                    "username": username,
                    "points": points
                }).execute()
                status = "🆕 Nouveau score enregistré"

            # 🖼️ Message de confirmation
            embed = discord.Embed(
                title="🌟 Mise à jour du Reiatsu",
                description=(
                    f"👤 Membre : {member.mention}\n"
                    f"✨ Nouveau score : `{points}` points\n\n"
                    f"{status}"
                ),
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(
                text=f"Modifié par {ctx.author.display_name}",
                icon_url=ctx.author.display_avatar.url
            )

            await ctx.send(embed=embed)

        except Exception as e:
            # 🚨 Gestion d’erreur
            await ctx.send(f"⚠️ Une erreur est survenue : `{e}`")

    # 🏷️ Catégorisation pour le système de help personnalisé
    def cog_load(self):
        self.changereiatsu.category = "Reiatsu"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(SetReiatsuPoints(bot))
    print("✅ Cog chargé : SetReiatsuPoints (catégorie = Reiatsu)")
