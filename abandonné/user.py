# ────────────────────────────────────────────────────────────────────────────────
# 📌 user.py — Commande interactive /user et !user
# Objectif : Embed complet avec toutes les infos disponibles sur un utilisateur
# Catégorie : Général
# Accès : Tous
# Cooldown : 1 utilisation / 3 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class UserInfo(commands.Cog):
    """
    Commande /user et !user — Affiche un embed complet et compact avec toutes les infos d’un utilisateur
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_user_embed(self, ctx_or_interaction, target: discord.Member):
        # Couleur selon rôle principal
        main_role = target.top_role if target.top_role and target.top_role.name != "@everyone" else None
        color = main_role.color if main_role else discord.Color.blurple()

        # Statut avec emoji
        status_emoji = {
            discord.Status.online: "🟢 En ligne",
            discord.Status.idle: "🌙 Inactif",
            discord.Status.dnd: "⛔ Ne pas déranger",
            discord.Status.offline: "⚫ Hors ligne"
        }.get(target.status, "⚪ Inconnu")

        # Activité actuelle
        activity_text = "Aucune"
        if target.activity:
            if isinstance(target.activity, discord.Game):
                activity_text = f"🎮 Joue à **{target.activity.name}**"
            elif isinstance(target.activity, discord.Streaming):
                activity_text = f"📺 Stream sur **{target.activity.name}**"
            elif isinstance(target.activity, discord.Spotify):
                activity_text = f"🎵 Écoute **{target.activity.title}** par {', '.join([a.name for a in target.activity.artists])}"
            else:
                activity_text = str(target.activity)

        # Badges Discord
        flags = target.public_flags
        badges = []
        if flags.staff: badges.append("🛡️ Staff")
        if flags.partner: badges.append("🤝 Partenaire")
        if flags.hypesquad: badges.append("🏠 HypeSquad")
        if flags.bug_hunter: badges.append("🐞 Bug Hunter")
        if flags.verified_bot_developer: badges.append("🤖 Dev Bot Vérifié")
        badges_text = ", ".join(badges) if badges else "Aucun"

        # Embed compact
        embed = discord.Embed(
            title=f"🔹 Infos pour {target.display_name}",
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="Nom complet", value=f"{target} (`{target.id}`)", inline=False)
        embed.add_field(name="Pseudo / Tag", value=f"{target.display_name} / #{target.discriminator}", inline=True)
        embed.add_field(name="Bot ?", value="✅" if target.bot else "❌", inline=True)
        embed.add_field(name="Compte créé le", value=target.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.add_field(name="Rejoint le serveur", value=target.joined_at.strftime("%d/%m/%Y %H:%M") if target.joined_at else "Inconnu", inline=True)
        embed.add_field(name=f"Rôles ({len(target.roles)-1})", value=", ".join([r.mention for r in target.roles if r.name != "@everyone"]) or "Aucun", inline=False)
        embed.add_field(name="Statut", value=status_emoji, inline=True)
        embed.add_field(name="Activité", value=activity_text, inline=True)
        embed.add_field(name="Badges", value=badges_text, inline=True)
        embed.set_footer(text=f"ID : {target.id}")

        # Envoi
        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed)
        else:
            await safe_send(ctx_or_interaction, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="user", description="Affiche un embed complet sur un utilisateur")
    @app_commands.describe(member="Membre à afficher (mention, ID ou pseudo)")
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def slash_user(self, interaction: discord.Interaction, member: discord.Member = None):
        try:
            target = member or interaction.user
            await self._send_user_embed(interaction, target)
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /user] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="user")
    @commands.cooldown(1, 3.0, commands.BucketType.user)
    async def prefix_user(self, ctx: commands.Context, member: discord.Member = None):
        try:
            target = member or ctx.author
            await self._send_user_embed(ctx.channel, target)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !user] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = UserInfo(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
