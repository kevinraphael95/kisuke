# ────────────────────────────────────────────────────────────────
#       🔄 COMMANDE ADMIN - RESET VOTES PERSOS (SUPABASE)       
# ────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from supabase_client import supabase  # Assure-toi que ce client est bien configuré

class ResetPersoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────
    # 🧹 Commande !resetperso (admin uniquement)
    # ⛔ Supprime tous les votes dans la table "perso_votes"
    # 🧊 Cooldown : 3s par admin
    # ──────────────────────────────────────────────────────
    @commands.command(
        name="tuprefreset",
        help="(Admin) Réinitialise tous les votes des personnages."
    )
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def resetperso(self, ctx):
        try:
            # ❌ Supprime tout sauf les entrées vides
            result = supabase.table("perso_votes").delete().neq("nom", "").execute()
            if result.get("error"):
                raise Exception(result["error"]["message"])
            await ctx.send("🗑️ Tous les votes ont été réinitialisés avec succès.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue lors de la réinitialisation :\n```{e}```")

    def cog_load(self):
        self.resetperso.category = "Fun"  # Ou "Admin" si tu crées une catégorie dédiée

# 🔌 Chargement automatique
async def setup(bot):
    cog = ResetPersoCommand(bot)
    for command in cog.get_commands():
        command.category = "Bleach"
    await bot.add_cog(cog)
