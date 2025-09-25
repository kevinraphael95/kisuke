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
import discord  # Librairie principale pour interagir avec Discord
from discord import app_commands  # Pour les commandes slash
from discord.ext import commands  # Pour les cogs et commandes classiques
from discord.ui import View, Button  # Pour les boutons interactifs
from dateutil import parser  # Pour parser les dates ISO depuis la DB
from datetime import datetime, timedelta  # Pour calculer les cooldowns et timers
import time  # Pour timestamp actuel
import json  # Pour charger les données JSON des classes

from utils.supabase_client import supabase  # Client Supabase pour DB
from utils.discord_utils import safe_send, safe_respond  # Envoi sécurisé anti-429

# ────────────────────────────────────────────────────────────────────────────────
# Infos intervalles de vitesse de spawn
# ────────────────────────────────────────────────────────────────────────────────
# Clé = nom interne (doit correspondre à la DB), valeur = texte affiché dans l'embed
SPAWN_SPEED_INTERVALS = {
    "Ultra_Rapide": "1-5 minutes",
    "Rapide": "5-20 minutes",
    "Normal": "30-60 minutes",
    "Lent": "5-10 heures"
}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Boutons interactifs Reiatsu
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuView(View):
    """
    Vue pour les boutons interactifs de Reiatsu :
    - Bouton pour aller au spawn
    - Bouton pour voir le classement
    """
    def __init__(self, author: discord.Member, spawn_link: str = None):
        super().__init__(timeout=120)  # Timeout global de 2 minutes
        self.author = author  # Auteur autorisé à interagir avec les boutons
        # Si un lien de spawn est fourni, ajout d’un bouton de redirection
        if spawn_link:
            self.add_item(Button(label="💠 Aller au spawn", style=discord.ButtonStyle.link, url=spawn_link))

    # ────────────────────────────────────────────────────────────────────────────
    # Bouton classement
    # ────────────────────────────────────────────────────────────────────────────
    @discord.ui.button(label="📊 Classement", style=discord.ButtonStyle.primary, custom_id="reiatsu:classement")
    async def classement_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Affiche le top 10 des joueurs par points de Reiatsu.
        Vérifie que l’utilisateur qui clique est bien l’auteur de la vue.
        """
        if interaction.user != self.author:
            return await interaction.response.send_message("❌ Tu ne peux pas utiliser ce bouton.", ephemeral=True)

        # 🔹 Récupération du top 10 dans la DB
        classement_data = supabase.table("reiatsu").select("user_id, points").order("points", desc=True).limit(10).execute()
        if not classement_data.data:
            return await interaction.response.send_message("Aucun classement disponible pour le moment.", ephemeral=True)

        # 🔹 Construction de la description de l'embed
        description = ""
        for i, entry in enumerate(classement_data.data, start=1):
            user_id = int(entry["user_id"])
            points = entry["points"]
            # Récupère le membre Discord si possible
            user = interaction.guild.get_member(user_id) if interaction.guild else None
            name = user.display_name if user else f"Utilisateur ({user_id})"
            description += f"**{i}. {name}** — {points} points\n"

        # 🔹 Création et envoi de l'embed
        embed = discord.Embed(title="📊 Classement Reiatsu", description=description, color=discord.Color.purple())
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # 🔹 Désactivation du bouton après clic
        button.disabled = True
        await interaction.message.edit(view=self)

    async def on_timeout(self):
        """Désactive tous les boutons lorsque la vue expire (après 2 minutes)."""
        for child in self.children:
            if isinstance(child, Button):
                child.disabled = True
        # Tente de mettre à jour le message si la vue est attachée
        try:
            message = self.message  # self.message est défini automatiquement quand la vue est envoyée
            if message:
                await message.edit(view=self)
        except Exception:
            pass


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuCommand(commands.Cog):
    """Commande /reiatsu et !reiatsu — Affiche le profil complet d’un joueur"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # Fonction interne pour afficher le profil
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_profile(self, ctx_or_interaction, author, guild, target_user):
        """
        Fonction principale pour construire et envoyer l'embed profil Reiatsu.
        - ctx_or_interaction : message ou interaction
        - author : utilisateur qui demande
        - guild : serveur
        - target_user : utilisateur ciblé (ou None pour l’auteur)
        """
        # Déterminer l’utilisateur cible
        user = target_user or author
        user_id = str(user.id)
        guild_id = str(guild.id) if guild else None

        # ───────────── Récupération des données du joueur ─────────────
        user_data = supabase.table("reiatsu").select(
            "points, classe, last_steal_attempt, steal_cd"
        ).eq("user_id", user_id).execute()
        data = user_data.data[0] if user_data.data else {}

        points = data.get("points", 0)  # Points de Reiatsu
        classe_nom = data.get("classe")  # Classe du joueur
        last_steal_str = data.get("last_steal_attempt")  # Dernier vol tenté
        steal_cd = data.get("steal_cd")  # Cooldown du vol

        # ───────────── Lecture des compétences depuis JSON ─────────────
        with open("data/classes.json", "r", encoding="utf-8") as f:
            CLASSES = json.load(f)

        if classe_nom and classe_nom in CLASSES:
            classe_text = (
                f"• Classe : **{classe_nom}**\n"
                f"• Compétence passive : {CLASSES[classe_nom]['Passive']}\n"
                f"• Compétence active : {CLASSES[classe_nom]['Active']}\n"
                "(les compétences actives ne sont pas ajoutées)"
            )
        else:
            classe_text = "Aucune classe sélectionnée.\nUtilise la commande `!classe` pour en choisir une."

        # ───────────── Gestion du cooldown de vol ─────────────
        cooldown_text = "Disponible ✅"
        if classe_nom and steal_cd is None:
            # Si le joueur a une classe mais pas de cooldown enregistré, on le définit
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

        # ───────────── Infos du salon de spawn ─────────────
        salon_text, temps_text, spawn_link = "❌", "❌", None
        if guild:
            config_data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
            config = config_data.data[0] if config_data.data else None

            salon_text = "❌ Aucun salon configuré"  # Valeur par défaut
            temps_text = "⚠️ Inconnu"  # Valeur par défaut
            spawn_speed_text = "⚠️ Inconnu"  # Valeur par défaut

            if config:
                # Tentative de récupération du salon Discord
                salon = guild.get_channel(int(config["channel_id"])) if config.get("channel_id") else None
                salon_text = salon.mention if salon else "⚠️ Salon introuvable"

                # ────── Vitesse de spawn ──────
                if config.get("spawn_speed"):
                    speed_key = config["spawn_speed"]
                    spawn_speed_text = f"{SPAWN_SPEED_INTERVALS.get(speed_key, '⚠️ Inconnu')} ({speed_key})"

                # ────── Gestion du temps restant avant spawn ──────
                if config.get("is_spawn"):
                    # Un Reiatsu est déjà présent
                    channel_id = config.get("channel_id")
                    msg_id = config.get("message_id")
                    if msg_id and channel_id:
                        spawn_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}"
                        temps_text = f"Un Reiatsu 💠 est **déjà apparu** !"
                    else:
                        temps_text = "Un Reiatsu 💠 est **déjà apparu** ! (Lien indisponible)"
                else:
                    # Aucun Reiatsu actif → calcul du temps restant
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
                        temps_text = "Un Reiatsu 💠 peut apparaître **à tout moment** !"

        # ───────────── Création de l'embed final ─────────────
        embed = discord.Embed(
            title=f"__**Profil de {user.display_name}**__",
            description=(
                f"• 💠 Reiatsu : **{points}**\n"
                f"• Cooldown vol : {cooldown_text}\n"
                f"(reiatsuvol pour voler du reiatsu à quelqu'un)\n"
                f"• Classe : {classe_nom or 'Aucune'}\n"
                f"(classe pour changer de classe)\n\n"
                f"• ℹ️ __**Infos Reiatsu**__\n"
                f"• 📍 Le reiatsu apparaît sur la salon : {salon_text}\n"
                f"• ⏱️ Intervalle entre deux apparitions : {spawn_speed_text}\n"
                f"• ⏳ Le prochain reiatsu va apparaître dans : {temps_text}"
            ),
            color=discord.Color.purple()
        )
        embed.set_footer(text="Utilise les boutons ci-dessous pour interagir.")
        view = ReiatsuView(author, spawn_link=spawn_link)

        # ───────────── Envoi du message selon contexte ─────────────
        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed, view=view)
        else:
            await safe_send(ctx_or_interaction, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # Commande SLASH /reiatsu
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="reiatsu", description="💠 Affiche le score de Reiatsu d’un membre (ou soi-même).")
    @app_commands.describe(member="Membre dont vous voulez voir le Reiatsu")
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)  # Cooldown 3s par utilisateur
    async def slash_reiatsu(self, interaction: discord.Interaction, member: discord.Member = None):
        try:
            await self._send_profile(interaction, interaction.user, interaction.guild, member)
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /reiatsu] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # Commande PREFIX !reiatsu ou !rts
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="reiatsu", aliases=["rts"])
    @commands.cooldown(1, 3.0, commands.BucketType.user)
    async def prefix_reiatsu(self, ctx: commands.Context, member: discord.Member = None):
        await self._send_profile(ctx.channel, ctx.author, ctx.guild, member)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuCommand(bot)
    # Ajout de la catégorie "Reiatsu" si non définie pour chaque commande
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
