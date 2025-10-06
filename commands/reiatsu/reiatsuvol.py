# ────────────────────────────────────────────────────────────────────────────────
# 📌 volreiatsu.py — Commande interactive /volreiatsu et !volreiatsu
# Objectif : Permet de voler 10% du Reiatsu d’un autre joueur avec probabilité de réussite
# Catégorie : Reiatsu
# Accès : Public
# Cooldown : 1 utilisation / 24h / utilisateur (persistant via Supabase)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta, timezone
from dateutil import parser
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond
import random

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Tables utilisées
# ────────────────────────────────────────────────────────────────────────────────
TABLES = {
    "reiatsu": {
        "description": "Table principale contenant les informations Reiatsu de chaque joueur : points, classe et cooldowns.",
        "colonnes": {
            "user_id": "BIGINT — Identifiant Discord unique du joueur (clé primaire)",
            "points": "INTEGER — Montant actuel de Reiatsu du joueur",
            "classe": "TEXT — Classe Reiatsu actuelle du joueur (ex: Voleur, Illusionniste...)",
            "steal_cd": "INTEGER — Cooldown personnalisé du vol en heures (par défaut 24h, 19h pour Voleur)",
            "last_steal_attempt": "TIMESTAMP WITH TIME ZONE — Dernière tentative de vol (sert au cooldown persistant)",
            "active_skill": "BOOLEAN — Indique si la compétence active du joueur (ex: vol garanti pour Voleur) est en cours d'effet"
        }
    }
}

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuVol(commands.Cog):
    """
    Commande /volreiatsu et !volreiatsu — Tente de voler du Reiatsu à un autre joueur
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _volreiatsu_logic(self, voleur: discord.Member, cible: discord.Member, channel: discord.abc.Messageable):
        voleur_id = int(voleur.id)
        cible_id = int(cible.id)

        # 📥 Récupération des données voleur
        voleur_res = supabase.table("reiatsu").select("*").eq("user_id", voleur_id).execute()
        if not voleur_res.data:
            await safe_send(channel, "⚠️ Données introuvables pour toi.")
            return
        voleur_data = voleur_res.data[0]
        voleur_classe = voleur_data.get("classe")
        voleur_cd = voleur_data.get("steal_cd") or 24

        # timezone-aware maintenant (UTC)
        now = datetime.now(tz=timezone.utc)
        dernier_vol_str = voleur_data.get("last_steal_attempt")
        if dernier_vol_str:
            try:
                dernier_vol = parser.parse(dernier_vol_str)
                if not dernier_vol.tzinfo:
                    dernier_vol = dernier_vol.replace(tzinfo=timezone.utc)
                else:
                    dernier_vol = dernier_vol.astimezone(timezone.utc)
                prochain_vol = dernier_vol + timedelta(hours=voleur_cd)
                if now < prochain_vol:
                    restant = prochain_vol - now
                    j = restant.days
                    h, rem = divmod(restant.seconds, 3600)
                    m, _ = divmod(rem, 60)
                    await safe_send(channel, f"⏳ Tu dois encore attendre **{j}j {h}h{m}m** avant de retenter.")
                    return
            except Exception as e:
                print(f"[WARN] Impossible de parser last_steal_attempt pour {voleur_id}: {e}")

        # 📥 Récupération des données cible
        cible_res = supabase.table("reiatsu").select("*").eq("user_id", cible_id).execute()
        if not cible_res.data:
            await safe_send(channel, "⚠️ Données introuvables pour la cible.")
            return
        cible_data = cible_res.data[0]

        voleur_points = voleur_data.get("points", 0) or 0
        cible_points = cible_data.get("points", 0) or 0
        cible_classe = cible_data.get("classe")

        if cible_points == 0:
            await safe_send(channel, f"⚠️ {cible.mention} n’a pas de Reiatsu à voler.")
            return
        if voleur_points == 0:
            await safe_send(channel, "⚠️ Tu dois avoir au moins **1 point** de Reiatsu pour tenter un vol.")
            return

        # 🎲 Calcul du vol
        montant = max(1, cible_points // 10)  # 10%

        # 🔹 Si voleur a activé son skill → vol garanti
        if voleur_classe == "Voleur" and voleur_data.get("active_skill", False):
            succes = True
            try:
                supabase.table("reiatsu").update({"active_skill": False}).eq("user_id", voleur_id).execute()
            except Exception as e:
                print(f"[WARN] Impossible de désactiver active_skill pour {voleur_id}: {e}")
        else:
            if voleur_classe == "Voleur":
                succes = random.random() < 0.67
                if random.random() < 0.15:
                    montant *= 2
            else:
                succes = random.random() < 0.25

        # Préparation du payload voleur (enregistre la tentative)
        payload_voleur = {"last_steal_attempt": now.isoformat()}
        if succes:
            payload_voleur["points"] = voleur_points + montant
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()

            # Si cible est illusionniste et illusion active -> elle ne perd rien
            if cible_classe == "Illusionniste" and random.random() < 0.5:
                await safe_send(channel, f"🩸 {voleur.mention} a volé **{montant}** points à {cible.mention}... mais c'était une illusion, {cible.mention} n'a rien perdu !")
            else:
                supabase.table("reiatsu").update({"points": max(0, cible_points - montant)}).eq("user_id", cible_id).execute()
                await safe_send(channel, f"🩸 {voleur.mention} a réussi à voler **{montant}** points de Reiatsu à {cible.mention} !")
        else:
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()
            await safe_send(channel, f"😵 {voleur.mention} a tenté de voler {cible.mention}... mais a échoué !")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="reiatsuvol",
        description="💠 Tente de voler 10% du Reiatsu d’un autre membre (25% de réussite). Cooldown : 24h."
    )
    async def slash_volreiatsu(self, interaction: discord.Interaction, cible: discord.Member):
        try:
            await interaction.response.defer()
            if interaction.user.id == cible.id:
                await safe_respond(interaction, "❌ Tu ne peux pas te voler toi-même.", ephemeral=True)
                return
            await self._volreiatsu_logic(interaction.user, cible, interaction.channel)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /reiatsuvol] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="reiatsuvol",
        aliases=["rtsv", "volreiatsu", "vrts"],
        help="💠 Tente de voler 10% du Reiatsu d’un autre membre. 25% de réussite. Cooldown : 24h."
    )
    async def prefix_volreiatsu(self, ctx: commands.Context, cible: discord.Member = None):
        try:
            if not cible:
                await safe_send(ctx.channel, "ℹ️ Utilisation : `!reiatsuvol @membre`")
                return
            if ctx.author.id == cible.id:
                await safe_send(ctx.channel, "❌ Tu ne peux pas te voler toi-même.")
                return
            await self._volreiatsu_logic(ctx.author, cible, ctx.channel)
        except Exception as e:
            print(f"[ERREUR !reiatsuvol] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuVol(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)



