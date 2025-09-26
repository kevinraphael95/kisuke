# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu.py — Commande interactive /reiatsu et !reiatsu
# Objectif : Affiche le score Reiatsu d’un membre, le salon de spawn, la vitesse et le temps restant
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
import os
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des classes depuis JSON
# ────────────────────────────────────────────────────────────────────────────────
CLASSES_JSON_PATH = os.path.join("data", "classes.json")

def load_classes():
    try:
        with open(CLASSES_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {CLASSES_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# Infos intervalles de vitesse de spawn
# ────────────────────────────────────────────────────────────────────────────────
SPAWN_SPEED_INTERVALS = {
    "Ultra_Rapide": "1-5 minutes",
    "Rapide": "5-20 minutes",
    "Normal": "30-60 minutes",
    "Lent": "5-10 heures"
}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue interactive Reiatsu
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuView(View):
    def __init__(self, author: discord.Member = None, spawn_link: str = None):
        super().__init__(timeout=None)
        self.author = author
        if spawn_link:
            self.add_item(Button(label="💠 Aller au spawn", style=discord.ButtonStyle.link, url=spawn_link))

    @discord.ui.button(label="📊 Classement", style=discord.ButtonStyle.primary, custom_id="reiatsu:classement")
    async def classement_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.author and interaction.user != self.author:
            return await interaction.response.send_message("❌ Tu ne peux pas utiliser ce bouton.", ephemeral=True)

        try:
            classement_data = supabase.table("reiatsu").select("user_id, points").order("points", desc=True).limit(10).execute()
        except Exception as e:
            print(f"[ERREUR DB] Impossible de récupérer le classement : {e}")
            return await interaction.response.send_message("❌ Erreur lors du chargement du classement.", ephemeral=True)

        if not classement_data.data:
            return await interaction.response.send_message("⚠️ Aucun classement disponible pour le moment.", ephemeral=True)

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
    """Commande /reiatsu et !reiatsu — Affiche le profil complet d’un joueur"""
    COOLDOWN = 3

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(ReiatsuView())
        self.user_cooldowns = {}  # user_id -> timestamp dernier usage

    async def _check_cooldown(self, user_id: int):
        now = time.time()
        last = self.user_cooldowns.get(user_id, 0)
        if now - last < self.COOLDOWN:
            return self.COOLDOWN - (now - last)
        self.user_cooldowns[user_id] = now
        return 0

    async def _send_profile(self, channel_or_interaction, author, guild, target_user):
        user = target_user or author
        user_id = int(user.id)
        guild_id = int(guild.id) if guild else None

        # Récupération des données utilisateur
        try:
            user_data = supabase.table("reiatsu").select(
                "points, classe, last_steal_attempt, steal_cd"
            ).eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[ERREUR DB] Lecture utilisateur échouée : {e}")
            return await safe_send(channel_or_interaction, "❌ Erreur lors de la récupération de tes données.")

        data = user_data.data[0] if user_data.data else {}
        points = data.get("points", 0)
        classe_nom = data.get("classe")
        last_steal_str = data.get("last_steal_attempt")
        steal_cd = data.get("steal_cd")

        # Chargement classes.json
        CLASSES = load_classes()
        classe_text = f"Aucune classe sélectionnée. Utilise `!classe` pour en choisir une."
        if classe_nom and classe_nom in CLASSES:
            classe_text = (
                f"• Classe : **{classe_nom}**\n"
                f"• Compétence passive : {CLASSES[classe_nom]['Passive']}\n"
                f"• Compétence active : {CLASSES[classe_nom]['Active']}\n"
                "(les compétences actives ne sont pas encore implémentées)"
            )

        # Cooldown de vol
        cooldown_text = "Disponible ✅"
        if last_steal_str and steal_cd:
            last_steal = parser.parse(last_steal_str)
            next_steal = last_steal + timedelta(hours=steal_cd)
            now_dt = datetime.utcnow()
            if now_dt < next_steal:
                restant = next_steal - now_dt
                h, m = divmod(int(restant.total_seconds() // 60), 60)
                cooldown_text = f"{restant.days}j {h}h{m}m" if restant.days else f"{h}h{m}m"

        # Récupération config serveur
        salon_text, spawn_speed_text, temps_text, spawn_link = "❌", "⚠️ Inconnu", "⚠️ Inconnu", None
        if guild:
            try:
                config_data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
            except Exception as e:
                print(f"[ERREUR DB] Lecture config échouée : {e}")
                config_data = None
            config = config_data.data[0] if config_data and config_data.data else None
            if config:
                salon = guild.get_channel(int(config.get("channel_id"))) if config.get("channel_id") else None
                salon_text = salon.mention if salon else "⚠️ Salon introuvable"
                speed_key = config.get("spawn_speed")
                spawn_speed_text = f"{SPAWN_SPEED_INTERVALS.get(speed_key, '⚠️ Inconnu')} ({speed_key})" if speed_key else spawn_speed_text

                if config.get("is_spawn") and config.get("message_id") and config.get("channel_id"):
                    spawn_link = f"https://discord.com/channels/{guild_id}/{config['channel_id']}/{config['message_id']}"
                    temps_text = "💠 Un Reiatsu est **déjà apparu** !"
                else:
                    last_spawn = config.get("last_spawn_at")
                    delay = config.get("spawn_delay", 1800)
                    if last_spawn:
                        remaining = int(parser.parse(last_spawn).timestamp() + delay - time.time())
                        if remaining <= 0:
                            temps_text = "💠 Un Reiatsu peut apparaître **à tout moment** !"
                        else:
                            minutes, seconds = divmod(remaining, 60)
                            temps_text = f"**{minutes}m {seconds}s**"
                    else:
                        temps_text = "💠 Un Reiatsu peut apparaître **à tout moment** !"

        # Création de l'embed
        embed = discord.Embed(
            title=f"__Profil de {user.display_name}__",
            description=(
                f"💠 **Reiatsu** : {points}\n"
                f"🔄 **Cooldown vol** : {cooldown_text}\n"
                f"🏷️ **Classe** : {classe_nom or 'Aucune'}\n\n"
                f"📍 Salon : {salon_text}\n"
                f"⏱️ Vitesse : {spawn_speed_text}\n"
                f"⏳ Prochain spawn : {temps_text}"
            ),
            color=discord.Color.purple()
        )
        embed.set_footer(text="Utilise les boutons ci-dessous pour interagir.")
        view = ReiatsuView(author, spawn_link=spawn_link)

        if isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.send_message(embed=embed, view=view)
        else:
            await safe_send(channel_or_interaction, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="reiatsu", description="💠 Affiche le score de Reiatsu d’un membre (ou soi-même).")
    @app_commands.describe(member="Membre dont vous voulez voir le Reiatsu")
    async def slash_reiatsu(self, interaction: discord.Interaction, member: discord.Member = None):
        remaining = await self._check_cooldown(interaction.user.id)
        if remaining > 0:
            return await safe_respond(interaction, f"⏳ Attends encore {remaining:.1f}s.", ephemeral=True)
        await self._send_profile(interaction, interaction.user, interaction.guild, member)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="reiatsu", aliases=["rts"])
    async def prefix_reiatsu(self, ctx: commands.Context, member: discord.Member = None):
        remaining = await self._check_cooldown(ctx.author.id)
        if remaining > 0:
            return await safe_send(ctx.channel, f"⏳ Attends encore {remaining:.1f}s.")
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
