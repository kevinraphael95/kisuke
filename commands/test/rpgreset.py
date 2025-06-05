# ────────────────────────────────────────────────────────────────
# ♻️ RPG RESET - SUPPRESSION DE LA SAUVEGARDE D'UN JOUEUR
# ────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from supabase_client import supabase

# ────────────────────────────────────────────────────────────────
# 📦 COG POUR RÉINITIALISER LA SAUVEGARDE D'UN JOUEUR
# ────────────────────────────────────────────────────────────────
class RPGReset(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────
    # 🧹 COMMANDE : !rpgreset [@membre]
    # Permet à un joueur de réinitialiser sa sauvegarde RPG
    # Un admin peut aussi réinitialiser celle d’un autre joueur
    # ──────────────────────────────────────────────────────
    @commands.command(
        name="rpgreset",
        help="♻️ Réinitialise ta progression RPG, ou celle d’un autre joueur (admin uniquement)."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rpgreset(self, ctx, membre: discord.Member = None):
        cible = membre or ctx.author

        # 🔒 Vérifie si l'utilisateur a le droit de reset un autre joueur
        if cible != ctx.author and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Tu n’as pas la permission de réinitialiser la progression des autres.")
            return

        # 🗑️ Suppression dans la base Supabase
        supabase.table("rpg_save").delete().eq("user_id", str(cible.id)).execute()

        # ✅ Confirmation
        if cible == ctx.author:
            await ctx.send("🗑️ Ta progression RPG a bien été réinitialisée.")
        else:
            await ctx.send(f"🛠️ La progression RPG de {cible.mention} a été **réinitialisée par un administrateur**.")

# ──────────────────────────────────────────────────────
# 🔌 CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────
async def setup(bot):
    cog = RPGReset(bot)
    for command in cog.get_commands():
        command.category = "Test"
    await bot.add_cog(cog)
