# ────────────────────────────────────────────────────────────────────────────────
# 📌 ReiatsuAdmin.py — Commande interactive !ReiatsuAdmin / !rtsa
# Objectif : Gérer les paramètres Reiatsu (définir, supprimer un salon, ou modifier les points d’un membre)
# Catégorie : Reiatsu
# Accès : Administrateur
# Cooldown : 1 utilisation / 5 secondes / utilisateur (sauf spawn : 3s)
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
from utils.discord_utils import safe_send, safe_reply, safe_edit, safe_delete

# ──────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ──────────────────────────────────────────────────────────────
class ReiatsuAdmin(commands.Cog):
    """
    Commande !ReiatsuAdmin / !rtsa — Gère Reiatsu : set, unset, change, spawn
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────
    # 🔹 Commande principale (groupe)
    # ──────────────────────────────────────────────────────────
    @commands.group(
        name="reiatsuadmin",
        aliases=["rtsa"],
        invoke_without_command=True,
        help="(Admin) Gère le Reiatsu : set, unset, change, spawn."
    )
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def reiatsuadmin(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🧪 Commande Reiatsu Admin",
            description=(
                "Voici les sous-commandes disponibles :\n\n"
                "`!!rtsa set` — Définit le salon de spawn de Reiatsu\n"
                "`!!rtsa unset` — Supprime le salon configuré\n"
                "`!!rtsa change @membre <points>` — Modifie les points d’un membre\n"
                "`!!rtsa spawn` — Force le spawn immédiat d’un Reiatsu"
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Réservé aux administrateurs")
        await safe_send(ctx, embed=embed)

    # ──────────────────────────────────────────────────────────
    # 🔹 Sous-commande : SET
    # ──────────────────────────────────────────────────────────
    @reiatsuadmin.command(name="set")
    @commands.has_permissions(administrator=True)
    async def set_reiatsu(self, ctx: commands.Context):
        try:
            guild_id = str(ctx.guild.id)
            channel_id = str(ctx.channel.id)
            now_iso = datetime.utcnow().isoformat()
            delay = random.randint(30, 60)

            data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
            if data.data:
                supabase.table("reiatsu_config").update({
                    "channel_id": channel_id,
                    "last_spawn_at": now_iso,
                    "delay_minutes": delay,
                    "en_attente": False,
                    "spawn_message_id": None
                }).eq("guild_id", guild_id).execute()
            else:
                supabase.table("reiatsu_config").insert({
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "last_spawn_at": now_iso,
                    "delay_minutes": delay,
                    "en_attente": False,
                    "spawn_message_id": None
                }).execute()

            await safe_send(ctx, f"✅ Le salon {ctx.channel.mention} est désormais configuré pour le spawn de Reiatsu.")
        except Exception as e:
            await safe_send(ctx, f"❌ Une erreur est survenue lors de la configuration : `{e}`")

    # ──────────────────────────────────────────────────────────
    # 🔹 Sous-commande : UNSET
    # ──────────────────────────────────────────────────────────
    @reiatsuadmin.command(name="unset")
    @commands.has_permissions(administrator=True)
    async def unset_reiatsu(self, ctx: commands.Context):
        try:
            guild_id = str(ctx.guild.id)
            res = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
            if res.data:
                supabase.table("reiatsu_config").delete().eq("guild_id", guild_id).execute()
                await safe_send(ctx, "🗑️ Le salon Reiatsu a été **supprimé** de la configuration.")
            else:
                await safe_send(ctx, "❌ Aucun salon Reiatsu n’était configuré sur ce serveur.")
        except Exception as e:
            await safe_send(ctx, f"❌ Une erreur est survenue lors de la suppression : `{e}`")

    # ──────────────────────────────────────────────────────────
    # 🔹 Sous-commande : CHANGE
    # ──────────────────────────────────────────────────────────
    @reiatsuadmin.command(name="change")
    @commands.has_permissions(administrator=True)
    async def change_reiatsu(self, ctx: commands.Context, member: discord.Member, points: int):
        if points < 0:
            await safe_send(ctx, "❌ Le score Reiatsu doit être un nombre **positif**.")
            return
        user_id = str(member.id)
        username = member.display_name
        try:
            data = supabase.table("reiatsu").select("user_id").eq("user_id", user_id).execute()
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
            await safe_send(ctx, embed=embed)
        except Exception as e:
            await safe_send(ctx, f"⚠️ Une erreur est survenue : `{e}`")

    # ──────────────────────────────────────────────────────────
    # 🔹 Sous-commande : SPAWN
    # ──────────────────────────────────────────────────────────
    @reiatsuadmin.command(name="spawn")
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def spawn_reiatsu(self, ctx: commands.Context):
        channel = ctx.channel
        embed = discord.Embed(
            title="💠 Un Reiatsu sauvage apparaît !",
            description="Cliquez sur la réaction 💠 pour l'absorber.",
            color=discord.Color.purple()
        )
        message = await safe_send(channel, embed=embed)
        if message is None:
            return
        try:
            await message.add_reaction("💠")
        except discord.HTTPException:
            pass

        def check(reaction, user):
            return reaction.message.id == message.id and str(reaction.emoji) == "💠" and not user.bot

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=40.0, check=check)
            await safe_send(channel, f"💠 {user.mention} a absorbé le Reiatsu !")
        except asyncio.TimeoutError:
            await safe_send(channel, "⏳ Le Reiatsu s’est dissipé dans l’air... personne ne l’a absorbé.")
        except Exception as e:
            await safe_send(channel, f"⚠️ Une erreur est survenue lors de l'attente de réaction : `{e}`")

# ──────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ──────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuAdmin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
