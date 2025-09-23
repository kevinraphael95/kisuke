# ──────────────────────────────────────────────────────────────
# 📌 ReiatsuAdmin.py — Commande interactive !ReiatsuAdmin / !rtsa
# Objectif : Gérer les paramètres Reiatsu (définir, supprimer un salon, ou modifier les points d’un membre)
# Catégorie : Reiatsu
# Accès : Administrateur
# Cooldown : 1 utilisation / 5 secondes / utilisateur (sauf spawn : 3s)
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
import asyncio
import random
from datetime import datetime
from discord.ext import commands
from discord import ui
import json
import os
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_reply, safe_edit, safe_delete

# ──────────────────────────────────────────────────────────────
# 📂 Chargement du JSON global
# ──────────────────────────────────────────────────────────────
CONFIG_PATH = os.path.join("data", "reiatsu_config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

SPAWN_SPEED_RANGES = CONFIG["SPAWN_SPEED_RANGES"]
DEFAULT_SPAWN_SPEED = CONFIG["DEFAULT_SPAWN_SPEED"]

# ──────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ──────────────────────────────────────────────────────────────
class ReiatsuAdmin(commands.Cog):
    """
    Commande !ReiatsuAdmin / !rtsa — Gère Reiatsu : set, unset, change, spawn, speed
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
        help="(Admin) Gère le Reiatsu : set, unset, change, spawn, speed."
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
                "`!!rtsa spawn` — Force le spawn immédiat d’un Reiatsu\n"
                "`!!rtsa speed` — Gère la vitesse du spawn"
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
            delay = random.randint(*SPAWN_SPEED_RANGES[DEFAULT_SPAWN_SPEED])
            default_speed = DEFAULT_SPAWN_SPEED

            data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
            if data.data:
                supabase.table("reiatsu_config").update({
                    "channel_id": channel_id,
                    "last_spawn_at": now_iso,
                    "spawn_delay": delay,
                    "spawn_speed": default_speed,
                    "is_spawn": False,
                    "message_id": None
                }).eq("guild_id", guild_id).execute()
            else:
                supabase.table("reiatsu_config").insert({
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "last_spawn_at": now_iso,
                    "spawn_delay": delay,
                    "spawn_speed": default_speed,
                    "is_spawn": False,
                    "message_id": None
                }).execute()

            await safe_send(ctx, f"✅ Le salon {ctx.channel.mention} est désormais configuré pour le spawn de Reiatsu avec vitesse par défaut **{default_speed}**.")
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
    # 🔹 Sous-commande : SPEED
    # ──────────────────────────────────────────────────────────
    @reiatsuadmin.command(name="speed")
    @commands.has_permissions(administrator=True)
    async def speed_reiatsu(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        res = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
        if not res.data:
            await safe_send(ctx, "❌ Aucun salon Reiatsu configuré pour ce serveur.")
            return

        config = res.data[0]
        current_delay = config.get("spawn_delay", SPAWN_SPEED_RANGES[DEFAULT_SPAWN_SPEED][1])
        current_speed_name = DEFAULT_SPAWN_SPEED
        for name, (min_delay, max_delay) in SPAWN_SPEED_RANGES.items():
            if min_delay <= current_delay <= max_delay:
                current_speed_name = name
                break

        embed = discord.Embed(
            title="⚡ Vitesse du spawn de Reiatsu",
            description=f"**Vitesse actuelle :** {current_speed_name} ({current_delay} s)",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="Vitesses possibles",
            value="\n".join([f"{name} → {min_d}-{max_d} s" for name, (min_d, max_d) in SPAWN_SPEED_RANGES.items()]),
            inline=False
        )

        class SpeedView(ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                for name in SPAWN_SPEED_RANGES:
                    if name != current_speed_name:
                        self.add_item(ui.Button(label=name, style=discord.ButtonStyle.primary, custom_id=f"speed_{name}"))

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                return interaction.user == ctx.author

            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True

        view = SpeedView()
        message = await safe_send(ctx, embed=embed, view=view)

        async def button_listener(interaction: discord.Interaction):
            new_speed_name = interaction.data["custom_id"].split("_", 1)[1]
            min_delay, max_delay = SPAWN_SPEED_RANGES[new_speed_name]
            new_delay = random.randint(min_delay, max_delay)
            supabase.table("reiatsu_config").update({
                "spawn_delay": new_delay,
                "spawn_speed": new_speed_name
            }).eq("guild_id", guild_id).execute()
            await interaction.response.edit_message(
                embed=discord.Embed(
                    title="✅ Vitesse du spawn modifiée",
                    description=f"Nouvelle vitesse : **{new_speed_name}** ({new_delay} s)",
                    color=discord.Color.green()
                ),
                view=None
            )

        for child in view.children:
            if isinstance(child, ui.Button):
                child.callback = button_listener

        self.bot.add_view(view)

# ──────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ──────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuAdmin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
