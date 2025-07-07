# ────────────────────────────────────────────────────────────────────────────────
# 📌 ReiatsuAdmin.py — Commande interactive !ReiatsuAdmin / !rtsa
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

# ──────────────────────────────────────────────────────────────
# 🔧 COG : ReiatsuAdmin
# ──────────────────────────────────────────────────────────────
class ReiatsuAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────
    # 🧭 COMMANDE PRINCIPALE : !ReiatsuAdmin / !rtsa
    # ──────────────────────────────────────────────────────────
    @commands.group(
        name="reiatsuadmin",
        aliases=["rtsa"],
        invoke_without_command=True,
        help="(Admin) Gère les paramètres Reiatsu (set, unset, change, spawn)."
    )
    @commands.has_permissions(administrator=True)
    async def ReiatsuAdmin(self, ctx: commands.Context):
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
        await ctx.send(embed=embed)

    # ──────────────────────────────────────────────────────────
    # ⚙️ SOUS-COMMANDE : SET
    # ──────────────────────────────────────────────────────────
    @ReiatsuAdmin.command(name="set")
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
    @ReiatsuAdmin.command(name="unset")
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
    @ReiatsuAdmin.command(name="change")
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
    # 💠 SOUS-COMMANDE : SPAWN
    # ──────────────────────────────────────────────────────────
    @ReiatsuAdmin.command(name="spawn")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Anti-spam : 3 sec
    async def spawn_reiatsu(self, ctx: commands.Context):
        channel = ctx.channel  # Le spawn se fait dans le salon courant

        embed = discord.Embed(
            title="💠 Un Reiatsu sauvage apparaît !",
            description="Cliquez sur la réaction 💠 pour l'absorber.",
            color=discord.Color.purple()
        )
        message = await channel.send(embed=embed)
        await message.add_reaction("💠")

        def check(reaction, user):
            return (
                reaction.message.id == message.id
                and str(reaction.emoji) == "💠"
                and not user.bot
            )

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=40.0, check=check)
            await channel.send(f"💠 {user.mention} a absorbé le Reiatsu !")
        except asyncio.TimeoutError:
            await channel.send("⏳ Le Reiatsu s’est dissipé dans l’air... personne ne l’a absorbé.")



# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuAdmin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
