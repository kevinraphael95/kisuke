# ────────────────────────────────────────────────────────────────────────────────
# 📌 heartbeat_admin.py — Commande !heartbeat <pause|resume|status|set|unset>
# Objectif : Gérer tout le heartbeat via une seule commande (pause, relance, statut, salon)
# Catégorie : Heartbeat
# Accès : Modérateur (permission admin requise)
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord  # Module Discord.py principal
from discord.ext import commands  # Extensions de commandes pour préfixe et cogs
from utils.discord_utils import safe_send  # Envoi "safe" pour éviter erreurs 429 ou suppression ratée

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class HeartbeatAdmin(commands.Cog):
    """
    Commande !heartbeat — Gère le heartbeat automatique (pause, relance, statut, salon).
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot  # Référence du bot pour accès aux autres cogs et méthodes
        self.supabase = bot.supabase  # Accès au client Supabase pour stocker les settings persistants

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="heartbeat",  # Nom de la commande préfixe
        aliases=["hb"],  # Alias secondaire pour la même commande
        help="(Admin) Gère le heartbeat : pause, resume, status, set, unset.",  # Aide rapide
        description="Gère le heartbeat automatique (pause, relance, statut, salon)."  # Description longue
    )
    @commands.has_permissions(administrator=True)  # ✅ Vérifie que l'utilisateur est admin
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)  # ⏳ Cooldown 5s/utilisateur
    async def heartbeat(self, ctx: commands.Context, action: str = None, channel: discord.TextChannel = None):
        """Commande préfixe pour gérer le heartbeat."""

        # Vérifie si une action a été fournie sinon affiche l'aide
        if not action:
            await safe_send(ctx, "❓ Utilisation : `!heartbeat pause|resume|status|set <#salon>|unset`")  # Message d'erreur si action manquante
            return  # Stoppe la commande

        action = action.lower()  # Convertit l'action en minuscule pour standardiser

        # ───────────── Pause / Resume ─────────────
        if action in ["pause", "p"]:  # Si action = pause ou p
            # Met à jour Supabase pour mettre le heartbeat en pause
            self.supabase.table("bot_settings").upsert({"key": "heartbeat_paused", "value": "true"}).execute()
            await safe_send(ctx, "⏸️ Heartbeat mis en pause.")  # Confirme à l'utilisateur

        elif action in ["resume", "r"]:  # Si action = resume ou r
            # Met à jour Supabase pour relancer le heartbeat
            self.supabase.table("bot_settings").upsert({"key": "heartbeat_paused", "value": "false"}).execute()
            await safe_send(ctx, "▶️ Heartbeat relancé.")  # Confirme à l'utilisateur

        # ───────────── Status ─────────────
        elif action in ["status", "stat", "s"]:  # Si action = status / stat / s
            # Récupère l'état actuel du heartbeat depuis Supabase
            res = self.supabase.table("bot_settings").select("value").eq("key", "heartbeat_paused").execute()
            paused = res.data and res.data[0]["value"].lower() == "true"  # Vérifie si la valeur est "true"
            # Prépare le message à envoyer selon l'état
            status_msg = "🔴 Le heartbeat est **en pause**." if paused else "🟢 Le heartbeat est **actif**."
            await safe_send(ctx, status_msg)  # Envoie le message de statut

        # ───────────── Set / Unset salon ─────────────
        elif action == "set":  # Si action = set
            if not channel:  # Vérifie si un salon a été fourni
                await safe_send(ctx, "❌ Tu dois mentionner un salon. Exemple : `!heartbeat set #général`")
                return  # Stoppe la commande si pas de salon
            # Enregistre l'ID du salon dans Supabase
            self.supabase.table("bot_settings").upsert({"key": "heartbeat_channel_id", "value": str(channel.id)}).execute()
            heartbeat_cog = self.bot.get_cog("HeartbeatTask")  # Récupère le cog HeartbeatTask s'il existe
            if heartbeat_cog:  # Si le cog existe
                heartbeat_cog.heartbeat_channel_id = channel.id  # Met à jour l'ID du salon dans le cog
            await safe_send(ctx, f"✅ Salon heartbeat défini : {channel.mention}")  # Confirme à l'utilisateur

        elif action == "unset":  # Si action = unset
            # Supprime le salon heartbeat dans Supabase
            self.supabase.table("bot_settings").upsert({"key": "heartbeat_channel_id", "value": ""}).execute()
            heartbeat_cog = self.bot.get_cog("HeartbeatTask")  # Récupère le cog HeartbeatTask
            if heartbeat_cog:  # Si le cog existe
                heartbeat_cog.heartbeat_channel_id = None  # Supprime l'ID du salon
            await safe_send(ctx, "🗑️ Salon heartbeat supprimé.")  # Confirme la suppression

        # ───────────── Action inconnue ─────────────
        else:  # Si aucune des actions ne correspond
            await safe_send(ctx, "❌ Action inconnue. Utilise `pause`, `resume`, `status`, `set`, ou `unset`.")  # Message d'erreur

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HeartbeatAdmin(bot)  # Instancie le cog
    for command in cog.get_commands():  # Parcourt toutes les commandes du cog
        if not hasattr(command, "category"):  # Si la commande n'a pas de catégorie
            command.category = "Admin"  # Définit la catégorie à Admin
    await bot.add_cog(cog)  # Ajoute le cog au bot
