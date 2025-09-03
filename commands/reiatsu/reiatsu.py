# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu.py — Commande interactive /reiatsu et !reiatsu
# Objectif : Affiche le score Reiatsu d’un membre, le salon de spawn et le temps restant
# Catégorie : Reiatsu
# Accès : Public
# Cooldown : 1 utilisation / 3 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from dateutil import parser
from datetime import datetime, timedelta
import time
import json

from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond  # Fonctions sécurisées anti-429

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Boutons interactifs Reiatsu
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuView(View):
    def __init__(self, author: discord.Member, spawn_link: str = None):
        super().__init__(timeout=None)
        self.author = author
        if spawn_link:
            self.add_item(Button(label="💠 Aller au spawn", style=discord.ButtonStyle.link, url=spawn_link))

    @discord.ui.button(label="📊 Classement", style=discord.ButtonStyle.primary, custom_id="reiatsu:classement")
    async def classement_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ Tu ne peux pas utiliser ce bouton.", ephemeral=True)

        classement_data = supabase.table("reiatsu").select("user_id, points").order("points", desc=True).limit(10).execute()
        if not classement_data.data:
            return await interaction.response.send_message("Aucun classement disponible pour le moment.", ephemeral=True)

        description = ""
        for i, entry in enumerate(classement_data.data, start=1):
            user_id = int(entry["user_id"])
            points = entry["points"]
            user = interaction.guild.get_member(user_id) if interaction.guild else None
            name = user.display_name if user else f"Utilisateur ({user_id})"
            description += f"**{i}. {name}** — {points} points\n"

        embed = discord.Embed(title="📊 Classement Reiatsu", description=description, color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuCommand(commands.Cog):
    """Commande /reiatsu et !reiatsu — Affiche le profil Reiatsu complet"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_profile(self, ctx_or_interaction, author, guild, target_user):
        user = target_user or author
        user_id = str(user.id)
        guild_id = str(guild.id) if guild else None

        user_data = supabase.table("reiatsu").select("points, classe, last_steal_attempt, steal_cd").eq("user_id", user_id).execute()
        data = user_data.data[0] if user_data.data else {}
        points = data.get("points", 0)
        classe_nom = data.get("classe")
        last_steal_str = data.get("last_steal_attempt")
        steal_cd = data.get("steal_cd")

        with open("data/classes.json", "r", encoding="utf-8") as f:
            CLASSES = json.load(f)

        if classe_nom and classe_nom in CLASSES:
            classe_text = f"• Classe : **{classe_nom}**\n• Compétence passive : {CLASSES[classe_nom]['Passive']}\n• Compétence active : {CLASSES[classe_nom]['Active']}\n(les compétences actives ne sont pas ajoutées)"
        else:
            classe_text = "Aucune classe sélectionnée.\nUtilise la commande `!classe` pour en choisir une."

        cooldown_text = "Disponible ✅"
        if classe_nom and steal_cd is None:
            steal_cd = 19 if classe_nom == "Voleur" else 24
            supabase.table("reiatsu").update({"steal_cd": steal_cd}).eq("user_id", user_id).execute()

        if last_steal_str and steal_cd:
            last_steal = parser.parse(last_steal_str)
            next_steal = last_steal + timedelta(hours=steal_cd)
            now = datetime.utcnow()
            if now < next_steal:
                restant = next_steal - now
                minutes_total = int(restant.total_seconds() // 60)
                h, m = divmod(minutes_total, 60)
                cooldown_text = f"{restant.days}j {h}h{m}m" if restant.days else f"{h}h{m}m"

        salon_text, temps_text, spawn_link = "❌", "❌", None
        if guild:
            config_data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
            config = config_data.data[0] if config_data.data else None
            salon_text = "❌ Aucun salon configuré"
            temps_text = "⚠️ Inconnu"
            if config:
                salon = guild.get_channel(int(config["channel_id"])) if config.get("channel_id") else None
                salon_text = salon.mention if salon else "⚠️ Salon introuvable"
                if config.get("en_attente"):
                    channel_id = config.get("channel_id")
                    msg_id = config.get("spawn_message_id")
                    if msg_id and channel_id:
                        spawn_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}"
                        temps_text = f"Un Reiatsu 💠 est **déjà apparu** !"
                    else:
                        temps_text = "Un Reiatsu 💠 est **déjà apparu** ! (Lien indisponible)"
                else:
                    last_spawn = config.get("last_spawn_at")
                    delay = config.get("delay_minutes", 1800)
                    if last_spawn:
                        remaining = int(parser.parse(last_spawn).timestamp() + delay - time.time())
                        if remaining <= 0:
                            temps_text = "💠 Un Reiatsu peut apparaître **à tout moment** !"
                        else:
                            minutes, seconds = divmod(remaining, 60)
                            temps_text = f"**{minutes}m {seconds}s**"
                    else:
                        temps_text = "Un Reiatsu 💠 peut apparaître **à tout moment** !"


        embed = discord.Embed(
            title=f"__**Profil de {user.display_name}**__",
            description=(
                f"• 💠 Reiatsu : **{points}**\n"
                f"• Cooldown vol : {cooldown_text} (reiatsuvol pour voler du reiatsu à quelqu'un)\n"
                f"• Classe : {classe_nom or 'Aucune'}\n"
                f"• Pouvoirs de : ?\n\n"
                f"• ℹ️ __**Infos Reiatsu**__\n"
                f"• 📍 Lieu d'apparition : {salon_text}\n"
                f"• ⏳ Temps avant apparition : {temps_text}"
            ),
            color=discord.Color.purple()
        )
        embed.set_footer(text="Utilise les boutons ci-dessous pour interagir.")
        view = ReiatsuView(author, spawn_link=spawn_link)

        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed, view=view)
        else:
            await safe_send(ctx_or_interaction, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="reiatsu", description="💠 Affiche le score de Reiatsu d’un membre (ou soi-même).")
    @app_commands.describe(member="Membre dont vous voulez voir le Reiatsu")
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def slash_reiatsu(self, interaction: discord.Interaction, member: discord.Member = None):
        try:
            await self._send_profile(interaction, interaction.user, interaction.guild, member)
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /reiatsu] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="reiatsu", aliases=["rts"])
    @commands.cooldown(1, 3.0, commands.BucketType.user)
    async def prefix_reiatsu(self, ctx: commands.Context, member: discord.Member = None):
        try:
            await ctx.message.delete()
        except:
            pass
        await self._send_profile(ctx.channel, ctx.author, ctx.guild, member)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)

