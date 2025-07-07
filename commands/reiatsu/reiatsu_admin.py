# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsuadmin.py — Commande interactive !reiatsuadmin / !rtsa
# Objectif : Gérer les paramètres Reiatsu (définir, supprimer un salon, ou modifier les points d’un membre)
# Catégorie : Reiatsu
# Accès : Administrateur
# ────────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
import asyncio
import random
from datetime import datetime
from discord.ext import commands
from supabase_client import supabase
from datetime import datetime, timedelta  # ✅ Ajout de timedelta


# ──────────────────────────────────────────────────────────────
# 🔧 COG : ReiatsuAdmin
# ──────────────────────────────────────────────────────────────
class ReiatsuAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────
    # 🧭 COMMANDE PRINCIPALE : !reiatsuadmin / !rtsa
    # ──────────────────────────────────────────────────────────
    @commands.group(
        name="reiatsuadmin",
        aliases=["rtsa"],
        invoke_without_command=True,
        help="(Admin) Gère les paramètres admin pour le Reiatsu (set, unset, change, autonow)."
    )
    @commands.has_permissions(administrator=True)
    async def reiatsuadmin(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🧪 Commande Reiatsu Admin",
            description=(
                "Voici les sous-commandes disponibles :\n\n"
                "`!!rtsa set` — Définit le salon de spawn de Reiatsu\n"
                "`!!rtsa unset` — Supprime le salon configuré\n"
                "`!!rtsa change @membre <points>` — Modifie les points d’un membre\n"
                "`!!rtsa autonow` — Force le spawn auto de Reiatsu à être imminent"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Réservé aux administrateurs")
        await ctx.send(embed=embed)

    # ──────────────────────────────────────────────────────────
    # ⚙️ SOUS-COMMANDE : SET
    # ──────────────────────────────────────────────────────────
    @reiatsuadmin.command(name="set")
    async def set_reiatsu(self, ctx: commands.Context):
        channel_id = ctx.channel.id
        guild_id = str(ctx.guild.id)
        now_iso = datetime.utcnow().isoformat()
        delay = random.randint(1800, 5400)

        data = supabase.table("reiatsu_config").select("id").eq("guild_id", guild_id).execute()
        if data.data:
            supabase.table("reiatsu_config").update({
                "channel_id": str(channel_id),
                "last_spawn_at": now_iso,
                "delay_minutes": delay,
                "en_attente": False,
                "spawn_message_id": None
            }).eq("guild_id", guild_id).execute()
        else:
            supabase.table("reiatsu_config").insert({
                "guild_id": guild_id,
                "channel_id": str(channel_id),
                "last_spawn_at": now_iso,
                "delay_minutes": delay,
                "en_attente": False,
                "spawn_message_id": None
            }).execute()

        await ctx.send(f"✅ Le salon actuel {ctx.channel.mention} est désormais configuré pour le spawn de Reiatsu.")

    # ──────────────────────────────────────────────────────────
    # 🗑️ SOUS-COMMANDE : UNSET
    # ──────────────────────────────────────────────────────────
    @reiatsuadmin.command(name="unset")
    async def unset_reiatsu(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        res = supabase.table("reiatsu_config").select("id").eq("guild_id", guild_id).execute()

        if res.data:
            supabase.table("reiatsu_config").delete().eq("guild_id", guild_id).execute()
            await ctx.send("🗑️ Le salon Reiatsu a été **supprimé** de la configuration.")
        else:
            await ctx.send("❌ Aucun salon Reiatsu n’était configuré sur ce serveur.")

    # ──────────────────────────────────────────────────────────
    # ✨ SOUS-COMMANDE : CHANGE
    # ──────────────────────────────────────────────────────────
    @reiatsuadmin.command(name="change")
    async def change_reiatsu(self, ctx: commands.Context, member: discord.Member, points: int):
        if points < 0:
            await ctx.send("❌ Le score Reiatsu doit être un nombre **positif**.")
            return

        user_id = str(member.id)
        username = member.display_name

        try:
            data = supabase.table("reiatsu").select("id").eq("user_id", user_id).execute()
            if data.data:
                supabase.table("reiatsu").update({"points": points}).eq("user_id", user_id).execute()
                status = "🔄 Score mis à jour"
            else:
                supabase.table("reiatsu").insert({
                    "user_id": user_id,
                    "username": username,
                    "points": points
                }).execute()
                status = "🆕 Nouveau score enregistré"

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
            await ctx.send(f"⚠️ Une erreur est survenue : `{e}`")

    # ──────────────────────────────────────────────────────────
    # ⏱️ SOUS-COMMANDE : AUTONOW
    # ──────────────────────────────────────────────────────────
    @reiatsuadmin.command(name="autonow")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def force_next_spawn_timer(self, ctx: commands.Context):
        """Avance le timer du prochain spawn automatique."""
        guild_id = str(ctx.guild.id)

        # 📦 Récupération de la configuration actuelle
        config = supabase.table("reiatsu_config").select("channel_id", "delay_minutes").eq("guild_id", guild_id).execute()

        if not config.data:
            await ctx.send("❌ Aucun salon Reiatsu n’a été configuré. Utilise `!rtsa set`.")
            return

        delay_minutes = config.data[0].get("delay_minutes", 30)  # Valeur par défaut = 30 min
        now = datetime.utcnow()

        # ⏪ On recule last_spawn_at pour que le système automatique déclenche un spawn dès le prochain check
        last_spawn_forced = now - timedelta(minutes=delay_minutes + 1)

        # 🛠️ Mise à jour dans la base Supabase
        supabase.table("reiatsu_config").update({
            "last_spawn_at": last_spawn_forced.isoformat(),
            "en_attente": False,
            "spawn_message_id": None
        }).eq("guild_id", guild_id).execute()

        await ctx.send("⏱️ Le timer a été avancé : le prochain **spawn automatique** est désormais **imminent**.")


# ──────────────────────────────────────────────────────────────
# 🔌 SETUP AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ReiatsuAdmin(bot))
    print("✅ Cog chargé : ReiatsuAdmin (catégorie = Reiatsu)")
