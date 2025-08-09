# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu.py — Commande interactive !reiatsu /reiatsu
# Objectif : Affiche le score Reiatsu d’un membre, le salon de spawn et le temps restant
# Catégorie : Reiatsu
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
from dateutil import parser
from datetime import datetime, timedelta
import time
from supabase_client import supabase
import json

from utils.discord_utils import safe_send  # <-- import fonctions anti 429

# ────────────────────────────────────────────────────────────────────────────────
# 🎯 Boutons interactifs
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuView(discord.ui.View):
    """
    Boutons interactifs pour la commande Reiatsu.
    """
    def __init__(self, author: discord.Member):
        super().__init__(timeout=None)  # View persistante
        self.author = author

    @discord.ui.button(label="📊 Classement", style=discord.ButtonStyle.primary, custom_id="reiatsu:classement")
    async def classement_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Autoriser seulement l'auteur du message
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ Tu ne peux pas utiliser ce bouton.", ephemeral=True)

        # ⚠️ Ici, à compléter avec la logique réelle de classement
        await interaction.response.send_message("📊 Classement Reiatsu : (à coder)", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Reiatsu2Command(commands.Cog):
    """
    Commande !reiatsu ou /reiatsu — Affiche ton score de Reiatsu, le salon et le temps avant le prochain spawn.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────────
    # ♻️ Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────────
    async def _reiatsu_core(self, channel, author, guild, target_user):
        user = target_user or author
        user_id = str(user.id)
        guild_id = str(guild.id) if guild else None

        # 📦 Requête : Données joueur
        user_data = supabase.table("reiatsu") \
            .select("points, classe, last_steal_attempt, steal_cd") \
            .eq("user_id", user_id) \
            .execute()
        data = user_data.data[0] if user_data.data else {}

        points = data.get("points", 0)
        classe_nom = data.get("classe")
        last_steal_str = data.get("last_steal_attempt")
        steal_cd = data.get("steal_cd")

        # 🔁 Chargement des infos de la classe
        with open("data/classes.json", "r", encoding="utf-8") as f:
            CLASSES = json.load(f)

        if classe_nom and classe_nom in CLASSES:
            classe_text = (
                f"• Classe : **{classe_nom}**\n"
                f"• Compétence passive : {CLASSES[classe_nom]['Passive']}\n"
                f"• Compétence active : {CLASSES[classe_nom]['Active']}\n"
                f"(les compétences actives ne sont pas ajoutées)"
            )
        else:
            classe_text = "Aucune classe sélectionnée.\nUtilise la commande `!classe` pour en choisir une."

        # 📦 Cooldown vol
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

        # 📦 Config serveur
        salon_text = "❌"
        temps_text = "❌"
        if guild:
            config_data = supabase.table("reiatsu_config") \
                .select("*") \
                .eq("guild_id", guild_id) \
                .execute()
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
                        link = f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}"
                        temps_text = f"Un Reiatsu 💠 est **déjà apparu** ! [Aller le prendre]({link})"
                    else:
                        temps_text = "Un Reiatsu 💠 est **déjà apparu** ! (Lien indisponible)"
                else:
                    last_spawn = config.get("last_spawn_at")
                    delay = config.get("delay_minutes", 1800)
                    if last_spawn:
                        last_ts = parser.parse(last_spawn).timestamp()
                        now_ts = time.time()
                        remaining = int((last_ts + delay) - now_ts)
                        if remaining <= 0:
                            temps_text = "💠 Un Reiatsu peut apparaître **à tout moment** !"
                        else:
                            minutes, seconds = divmod(remaining, 60)
                            temps_text = f"**{minutes}m {seconds}s**"
                    else:
                        temps_text = "Un Reiatsu 💠 peut apparaître **à tout moment** !"

        # 📋 Embed
        embed = discord.Embed(
            title="__**💠 Profil**__",
            description=(
                f"**{user.display_name}** a actuellement :\n"
                f"**{points}** points de Reiatsu\n"
                f"• 🕵️ Cooldown vol : {cooldown_text} (!!reiatsuvol pour voler du reiatsu à quelqu'un)\n\n"
                f"__**Classe**__\n"
                f"{classe_text}\n\n"
                f"__**Spawn du reiatsu**__\n"
                f"• 📍 Lieu d'apparition : {salon_text}\n"
                f"• ⏳ Temps avant apparition : {temps_text}"
            ),
            color=discord.Color.purple()
        )
        embed.set_footer(text="Utilise les boutons ci-dessous pour interagir.")

        # ✅ Envoi avec bouton
        view = ReiatsuView(author)
        await safe_send(channel, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────────────
    # ⌨️ Commande préfixe
    # ────────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="reiatsu",
        aliases=["rts"],
        help="💠 Affiche le score de Reiatsu d’un membre (ou soi-même).",
        description="Affiche le score, le salon de spawn et le temps restant avant le prochain Reiatsu."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def reiatsu(self, ctx: commands.Context, member: discord.Member = None):
        await self._reiatsu_core(ctx.channel, ctx.author, ctx.guild, member)

    # ────────────────────────────────────────────────────────────────────────────────
    # 💬 Commande slash
    # ────────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="reiatsu",
        description="💠 Affiche le score de Reiatsu d’un membre (ou soi-même)."
    )
    @app_commands.describe(member="Membre dont voir le score (optionnel)")
    async def reiatsu_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        await self._reiatsu_core(interaction.channel, interaction.user, interaction.guild, member)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Reiatsu2Command(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
