# ──────────────────────────────────────────────────────────────
# 📁 REIATSU - SALON CONFIGURÉ
# ──────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
from supabase_client import supabase

# ──────────────────────────────────────────────────────────────
# 🔧 COG : ReiatsuChannelCommand
# ──────────────────────────────────────────────────────────────
class ReiatsuChannelCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot  # 🔌 Référence au bot

    # ──────────────────────────────────────────────────────────
    # 💬 COMMANDE : !reiatsuchannel
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="reiatsuchannel",
        aliases=["rtschannel"],
        help="💠 Affiche le salon configuré pour le spawn de Reiatsu. (Admin uniquement)"
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🧊 Cooldown 3s
    @commands.has_permissions(administrator=True)  # 🛡️ Admin requis
    async def reiatsuchannel(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)  # 🏷️ Identifiant du serveur

        # 📦 Requête vers Supabase
        data = supabase.table("reiatsu_config") \
                       .select("channel_id") \
                       .eq("guild_id", guild_id) \
                       .execute()

        if data.data:
            channel_id = int(data.data[0]["channel_id"])
            channel = self.bot.get_channel(channel_id)

            # ✅ Salon valide
            if channel:
                await ctx.send(f"💠 Le salon configuré pour le spawn de Reiatsu est : {channel.mention}")
            # ⚠️ Salon introuvable
            else:
                await ctx.send("⚠️ Le salon configuré n'existe plus ou n'est pas accessible.")
        else:
            await ctx.send("❌ Aucun salon Reiatsu n’a encore été configuré avec `!setreiatsu`.")

    # 🏷️ Attribution de la catégorie
    def cog_load(self):
        self.reiatsuchannel.category = "Reiatsu"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ReiatsuChannelCommand(bot))
    print("✅ Cog chargé : ReiatsuChannelCommand (catégorie = Reiatsu)")
