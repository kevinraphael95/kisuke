# ────────────────────────────────────────────────────────────────────────────────
# 📌 volreiatsu.py — Commande interactive volreiatsu (préfixe + slash)
# Objectif : Voler 10% du Reiatsu d’un autre joueur avec 25% (40% si voleur) de réussite.
# Catégorie : VAACT
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from supabase_client import supabase
import random
from utils.discord_utils import safe_send  # <-- Utilitaire safe_send

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuVol(commands.Cog):
    """
    Commande volreiatsu — Tente de voler 10% du Reiatsu d’un autre joueur (25% ou 40% si classe voleur)
    Fonctionne en commande préfixée et en slash command.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Commande préfixée
    @commands.command(
        name="reiatsuvol",
        aliases=["rtsv", "volreiatsu", "vrts"],
        help="💠 Tente de voler 10% du Reiatsu d’un autre membre. 25% de réussite (40% si Voleur). Cooldown : 24h."
    )
    async def volreiatsu_prefix(self, ctx: commands.Context, cible: discord.Member = None):
        await self._volreiatsu_logic(ctx, cible, is_slash=False)

    # Commande slash
    @app_commands.command(
        name="volreiatsu",
        description="Tente de voler 10% du Reiatsu d’un autre membre. 25% de réussite (40% si Voleur). Cooldown : 24h."
    )
    @app_commands.describe(cible="Le membre à qui tu souhaites voler du Reiatsu")
    async def volreiatsu_slash(self, interaction: discord.Interaction, cible: discord.Member):
        await self._volreiatsu_logic(interaction, cible, is_slash=True)

    # Logique commune pour les 2 types de commandes
    async def _volreiatsu_logic(self, ctx_or_inter, cible: discord.Member, is_slash: bool):
        # Définition du channel et auteur selon type d'interaction
        if is_slash:
            channel = ctx_or_inter.channel
            voleur = ctx_or_inter.user
        else:
            channel = ctx_or_inter.channel
            voleur = ctx_or_inter.author

        voleur_id = str(voleur.id)

        # Récupération données voleur
        voleur_data = supabase.table("reiatsu").select("*").eq("user_id", voleur_id).execute()
        if not voleur_data.data:
            await safe_send(channel, "⚠️ Données introuvables pour toi.")
            return
        voleur_data = voleur_data.data[0]

        voleur_classe = voleur_data.get("classe")
        voleur_cd = voleur_data.get("steal_cd", 24)
        now = datetime.utcnow()
        dernier_vol_str = voleur_data.get("last_steal_attempt")

        # Gestion cooldown
        if dernier_vol_str:
            dernier_vol = datetime.fromisoformat(dernier_vol_str)
            prochain_vol = dernier_vol + timedelta(hours=voleur_cd)
            if now < prochain_vol:
                restant = prochain_vol - now
                j = restant.days
                h, rem = divmod(restant.seconds, 3600)
                m, _ = divmod(rem, 60)
                await safe_send(channel, f"⏳ Tu dois encore attendre **{j}j {h}h{m}m** avant de retenter.")
                return

        # Vérification cible
        if cible is None:
            await safe_send(channel, "ℹ️ Tu dois mentionner un membre pour tenter de voler du Reiatsu.")
            return
        if voleur.id == cible.id:
            await safe_send(channel, "❌ Tu ne peux pas te voler toi-même.")
            return

        cible_id = str(cible.id)

        # Récupération données cible
        cible_data = supabase.table("reiatsu").select("*").eq("user_id", cible_id).execute()
        if not cible_data.data:
            await safe_send(channel, "⚠️ Données introuvables pour la cible.")
            return
        cible_data = cible_data.data[0]

        voleur_points = voleur_data.get("points", 0)
        cible_points = cible_data.get("points", 0)
        cible_classe = cible_data.get("classe")

        if cible_points == 0:
            await safe_send(channel, f"⚠️ {cible.mention} n’a pas de Reiatsu à voler.")
            return
        if voleur_points == 0:
            await safe_send(channel, "⚠️ Tu dois avoir au moins **1 point** de Reiatsu pour tenter un vol.")
            return

        # Calcul du vol
        montant = max(1, cible_points // 10)  # 10%
        if voleur_classe == "Voleur" and random.random() < 0.5:  # 50% chance double gain
            montant *= 2

        succes_chance = 0.40 if voleur_classe == "Voleur" else 0.25
        succes = random.random() < succes_chance

        # Préparation update voleur cooldown + points éventuels
        payload_voleur = {"last_steal_attempt": now.isoformat()}

        if succes:
            # Succès : ajout points voleur
            payload_voleur["points"] = voleur_points + montant
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()

            # Effet Illusionniste
            if cible_classe == "Illusionniste" and random.random() < 0.5:
                await safe_send(channel, f"🩸 {voleur.mention} a volé **{montant}** points à {cible.mention}... mais c'était une illusion, {cible.mention} n'a rien perdu !")
            else:
                # Retrait points cible
                supabase.table("reiatsu").update({
                    "points": max(0, cible_points - montant)
                }).eq("user_id", cible_id).execute()
                await safe_send(channel, f"🩸 {voleur.mention} a réussi à voler **{montant}** points de Reiatsu à {cible.mention} !")
        else:
            # Échec : maj cooldown seulement
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()
            await safe_send(channel, f"😵 {voleur.mention} a tenté de voler {cible.mention}... mais a échoué !")

        # Si slash interaction, on doit répondre ou defer (ici on répond par safe_send donc pas besoin defer)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuVol(bot)
    bot.tree.add_command(cog.volreiatsu_slash)  # Ajout commande slash
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
