# ──────────────────────────────────────────────────────────────
# 📁 REIATSU ─ Forcer l’apparition
# ──────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
from datetime import datetime
from supabase_client import supabase

# ──────────────────────────────────────────────────────────────
# 🔧 COG : ForceSpawnCommand
# ──────────────────────────────────────────────────────────────
class ForceSpawnCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # 🔌 Stockage de l’instance du bot

    # ──────────────────────────────────────────────────────────
    # 🌀 COMMANDE : !forcespawn
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="forcespawn",
        help="(Admin) Force le spawn immédiat d’un Reiatsu."
    )
    @commands.has_permissions(administrator=True)  # 🔐 Réservé aux administrateurs
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.guild)  # 🧊 Cooldown global 10s
    async def forcespawn(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)

        # 🔍 Vérifie que la config existe pour ce serveur
        config = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()

        if not config.data:
            await ctx.send("❌ Ce serveur n’a pas encore de configuration Reiatsu. Utilisez `!setreiatsu`.")
            return

        # 🕒 Définition de l’heure actuelle pour le reset du timer
        now = datetime.utcnow().isoformat()

        # ⚙️ Mise à jour des données dans Supabase
        supabase.table("reiatsu_config").update({
            "last_spawn_at": None,     # ⏱️ Réinitialisation du dernier spawn
            "delay_minutes": 1         # 🔁 Délai minimum pour que le bot déclenche le prochain spawn
        }).eq("guild_id", guild_id).execute()

        # ✅ Confirmation visuelle
        embed = discord.Embed(
            title="💠 Apparition forcée du Reiatsu",
            description="Un **Reiatsu** va apparaître **dans moins d'une minute** !",
            color=discord.Color.teal()
        )
        embed.set_footer(text=f"Déclenché par {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    # 🏷️ Catégorisation pour help personnalisé
    def cog_load(self):
        self.forcespawn.category = "Reiatsu"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ForceSpawnCommand(bot))
    print("✅ Cog chargé : ForceSpawnCommand (catégorie = Reiatsu)")
