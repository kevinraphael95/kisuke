# ────────────────────────────────────────────────────────────────────────────────
# 📌 volreiatsu.py — Commande préfixe et slash !volreiatsu / /volreiatsu
# Objectif : Tenter de voler 5% du Reiatsu d’un autre joueur avec 25% de réussite.
# Catégorie : Reiatsu
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
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal ReiatsuVol
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuVol(commands.Cog):
    """
    Cog pour la commande de vol de Reiatsu,
    avec commande préfixe et slash.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --------------------------
    # Commande préfixe !volreiatsu
    # --------------------------
    @commands.command(
        name="volreiatsu",
        aliases=["reiatsuvol", "vrts", "rtsv"],
        help="💠 Tente de voler 5% du Reiatsu d’un autre membre. 25% de réussite. Cooldown 24h.",
        description="Commande de vol de Reiatsu avec échec possible, cooldown 24h."
    )
    async def volreiatsu(self, ctx: commands.Context, cible: discord.Member = None):
        await self.process_steal(ctx, cible, is_slash=False)

    # --------------------------
    # Commande slash /volreiatsu
    # --------------------------
    @app_commands.command(
        name="volreiatsu",
        description="💠 Tente de voler 5% du Reiatsu d’un autre membre. 25% de réussite. Cooldown 24h."
    )
    @app_commands.describe(cible="Membre dont tu veux voler le Reiatsu")
    async def slash_volreiatsu(self, interaction: discord.Interaction, cible: discord.Member):
        await self.process_steal(interaction, cible, is_slash=True)

    # On ajoute la commande slash au bot
    async def cog_load(self):
        self.bot.tree.add_command(self.slash_volreiatsu)

    # --------------------------
    # Méthode commune pour gérer vol
    # --------------------------
    async def process_steal(self, ctx_or_inter, cible, is_slash: bool):
        # Fonction interne pour envoyer réponse simple ou embed
        async def respond(message=None, *, embed=None, ephemeral=False):
            if is_slash:
                await safe_respond(ctx_or_inter, message, embed=embed, ephemeral=ephemeral)
            else:
                if embed:
                    await safe_send(ctx_or_inter.channel, embed=embed)
                else:
                    await safe_send(ctx_or_inter.channel, message)

        # Récupération de l'auteur et channel
        if is_slash:
            user = ctx_or_inter.user
        else:
            user = ctx_or_inter.author

        user_id = str(user.id)

        # Vérification cible
        if cible is None:
            return await respond("ℹ️ Tu dois mentionner un membre cible (ex: @membre).", ephemeral=True)

        if user.id == cible.id:
            return await respond("❌ Tu ne peux pas te voler toi-même.", ephemeral=True)

        cible_id = str(cible.id)

        # Récupération données voleur
        voleur_data_resp = supabase.table("reiatsu").select("*").eq("user_id", user_id).execute()
        if not voleur_data_resp.data:
            return await respond("⚠️ Données introuvables pour toi.", ephemeral=True)
        voleur_data = voleur_data_resp.data[0]

        # Récupération données cible
        cible_data_resp = supabase.table("reiatsu").select("*").eq("user_id", cible_id).execute()
        if not cible_data_resp.data:
            return await respond("⚠️ Données introuvables pour la cible.", ephemeral=True)
        cible_data = cible_data_resp.data[0]

        now = datetime.utcnow()
        voleur_classe = voleur_data.get("classe")
        voleur_cd = voleur_data.get("steal_cd", 24)
        dernier_vol_str = voleur_data.get("last_steal_attempt")

        # Cooldown
        if dernier_vol_str:
            dernier_vol = datetime.fromisoformat(dernier_vol_str)
            prochain_vol = dernier_vol + timedelta(hours=voleur_cd)
            if now < prochain_vol:
                restant = prochain_vol - now
                j = restant.days
                h, rem = divmod(restant.seconds, 3600)
                m, _ = divmod(rem, 60)
                return await respond(f"⏳ Tu dois encore attendre **{j}j {h}h{m}m** avant de retenter.", ephemeral=True)

        voleur_points = voleur_data.get("points", 0)
        cible_points = cible_data.get("points", 0)
        cible_classe = cible_data.get("classe")

        # Vérifications points
        if cible_points == 0:
            return await respond(f"⚠️ {cible.mention} n’a pas de Reiatsu à voler.", ephemeral=True)

        if voleur_points == 0:
            return await respond("⚠️ Tu dois avoir au moins **1 point** de Reiatsu pour tenter un vol.", ephemeral=True)

        # Calcul vol
        montant = max(1, cible_points * 5 // 100)  # 5%
        if voleur_classe == "Voleur" and random.random() < 0.5:
            montant *= 2

        if voleur_classe == "Voleur":
            succes = random.random() < 0.40  # 40%
        else:
            succes = random.random() < 0.25  # 25%

        payload_voleur = {"last_steal_attempt": now.isoformat()}
        embed = discord.Embed(color=discord.Color.purple())
        embed.set_author(name=f"Vol de Reiatsu - {user.display_name}", icon_url=user.display_avatar.url)

        if succes:
            payload_voleur["points"] = voleur_points + montant
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", user_id).execute()

            if cible_classe == "Illusionniste" and random.random() < 0.5:
                contenu = f"🩸 {user.mention} a volé **{montant}** points à {cible.mention}... mais c'était une illusion, {cible.mention} n'a rien perdu !"
                embed.description = contenu
            else:
                supabase.table("reiatsu").update({
                    "points": max(0, cible_points - montant)
                }).eq("user_id", cible_id).execute()
                contenu = f"🩸 {user.mention} a réussi à voler **{montant}** points de Reiatsu à {cible.mention} !"
                embed.description = contenu
        else:
            # Échec : update cooldown seulement
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", user_id).execute()
            contenu = f"😵 {user.mention} a tenté de voler {cible.mention}... mais a échoué !"
            embed.description = contenu

        return await respond(embed=embed)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuVol(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
