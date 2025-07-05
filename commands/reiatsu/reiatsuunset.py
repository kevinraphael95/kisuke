# ──────────────────────────────────────────────────────────────
# 📁 REIATSU - SUPPRESSION DU SALON CONFIGURÉ
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from supabase_client import supabase

# ──────────────────────────────────────────────────────────────
# 🔧 COG : UnsetReiatsuCommand
# ──────────────────────────────────────────────────────────────
class UnsetReiatsuCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────
    # 🗑️ COMMANDE : unsetreiatsu
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="reiatsuunset",
        aliases=["rtsunset"],
        help="Supprime le salon configuré pour le spawn de Reiatsu. (Admin uniquement)"
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def unsetreiatsu(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)

        res = supabase.table("reiatsu_config").select("id").eq("guild_id", guild_id).execute()

        if res.data:
            supabase.table("reiatsu_config").delete().eq("guild_id", guild_id).execute()
            await ctx.send("🗑️ Le salon Reiatsu a été **supprimé** de la configuration.")
        else:
            await ctx.send("❌ Aucun salon Reiatsu n’était configuré sur ce serveur.")

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = UnsetReiatsuCommand(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
    print("✅ Cog chargé : UnsetReiatsuCommand (Suppression)")
