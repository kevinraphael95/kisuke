# ────────────────────────────────────────────────────────────────────────────────
# 📌 volreiatsu.py — Commande interactive !volreiatsu et /reiatsuvol
# Objectif : Permet de voler 5% du Reiatsu d’un autre joueur avec 25% de réussite.
# Catégorie : VAACT
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from supabase_client import supabase
import random

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuVol(commands.Cog):
    """
    Commande !reiatsuvol & /reiatsuvol — Tente de voler du Reiatsu à un autre joueur (25% de chance)
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _voler_reiatsu(self, voleur: discord.User, cible: discord.User, ctx_or_inter):
        """
        Fonction interne unique pour la logique du vol de Reiatsu.
        ctx_or_inter peut être un Context (commande prefix) ou Interaction (slash command).
        """
        voleur_id = str(voleur.id)
        cible_id = str(cible.id)

        # Récupération données voleur
        voleur_data = supabase.table("reiatsu").select("*").eq("user_id", voleur_id).execute()
        if not voleur_data.data:
            await self._send(ctx_or_inter, "⚠️ Données introuvables pour toi.")
            return
        voleur_data = voleur_data.data[0]

        # Récupération données cible
        cible_data = supabase.table("reiatsu").select("*").eq("user_id", cible_id).execute()
        if not cible_data.data:
            await self._send(ctx_or_inter, "⚠️ Données introuvables pour la cible.")
            return
        cible_data = cible_data.data[0]

        # Check cooldown
        voleur_cd = voleur_data.get("steal_cd", 24)
        dernier_vol_str = voleur_data.get("last_steal_attempt")
        now = datetime.utcnow()

        if dernier_vol_str:
            dernier_vol = datetime.fromisoformat(dernier_vol_str)
            prochain_vol = dernier_vol + timedelta(hours=voleur_cd)
            if now < prochain_vol:
                restant = prochain_vol - now
                j = restant.days
                h, m = divmod(restant.seconds // 60, 60)
                await self._send(ctx_or_inter, f"⏳ Tu dois encore attendre **{j}j {h}h{m}m** avant de retenter.")
                return

        # Vérifications basiques
        if voleur.id == cible.id:
            await self._send(ctx_or_inter, "❌ Tu ne peux pas te voler toi-même.")
            return

        voleur_points = voleur_data.get("points", 0)
        cible_points = cible_data.get("points", 0)
        voleur_classe = voleur_data.get("classe")
        cible_classe = cible_data.get("classe")

        if cible_points == 0:
            await self._send(ctx_or_inter, f"⚠️ {cible.mention if hasattr(cible, 'mention') else cible.name} n’a pas de Reiatsu à voler.")
            return
        if voleur_points == 0:
            await self._send(ctx_or_inter, "⚠️ Tu dois avoir au moins **1 point** de Reiatsu pour tenter un vol.")
            return

        # Calcul du vol (5% au lieu de 10% car demandé)
        montant = max(1, cible_points // 20)  # 5%
        if voleur_classe == "Voleur" and random.random() < 0.5:
            montant *= 2

        succes_prob = 0.40 if voleur_classe == "Voleur" else 0.25
        succes = random.random() < succes_prob

        # Payload cooldown
        payload_voleur = {
            "last_steal_attempt": now.isoformat()
        }

        if succes:
            # Succès : ajouter points au voleur
            payload_voleur["points"] = voleur_points + montant
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()

            if cible_classe == "Illusionniste" and random.random() < 0.5:
                await self._send(ctx_or_inter,
                    f"🩸 {voleur.mention if hasattr(voleur, 'mention') else voleur.name} a volé **{montant}** points à "
                    f"{cible.mention if hasattr(cible, 'mention') else cible.name}... mais c'était une illusion, {cible.mention if hasattr(cible, 'mention') else cible.name} n'a rien perdu !")
            else:
                supabase.table("reiatsu").update({
                    "points": max(0, cible_points - montant)
                }).eq("user_id", cible_id).execute()
                await self._send(ctx_or_inter,
                    f"🩸 {voleur.mention if hasattr(voleur, 'mention') else voleur.name} a réussi à voler **{montant}** points de Reiatsu à "
                    f"{cible.mention if hasattr(cible, 'mention') else cible.name} !")
        else:
            # Échec : update cooldown uniquement
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()
            await self._send(ctx_or_inter,
                f"😵 {voleur.mention if hasattr(voleur, 'mention') else voleur.name} a tenté de voler "
                f"{cible.mention if hasattr(cible, 'mention') else cible.name}... mais a échoué !")

    async def _send(self, ctx_or_inter, message: str):
        """Fonction helper pour envoyer un message selon le type (Context ou Interaction)."""
        if isinstance(ctx_or_inter, commands.Context):
            await ctx_or_inter.send(message)
        elif isinstance(ctx_or_inter, discord.Interaction):
            if ctx_or_inter.response.is_done():
                await ctx_or_inter.followup.send(message)
            else:
                await ctx_or_inter.response.send_message(message)

    # ─────────────── Commande prefixée ───────────────
    @commands.command(
        name="reiatsuvol",
        aliases=["rtsv", "volreiatsu", "vrts"],
        help="💠 Tente de voler 5% du Reiatsu d’un autre membre. 25% de réussite. Cooldown : 24h.",
        description="Commande de vol de Reiatsu avec échec possible. Pas de perte en cas d’échec. Cooldown persistant."
    )
    async def volreiatsu(self, ctx: commands.Context, cible: discord.Member = None):
        if cible is None:
            await ctx.send("ℹ️ Tu dois faire `!!volreiatsu @membre` pour tenter de voler du Reiatsu.")
            return
        await self._voler_reiatsu(ctx.author, cible, ctx)

    # ─────────────── Commande slash ───────────────
    @app_commands.command(
        name="reiatsuvol",
        description="Tente de voler 5% du Reiatsu d’un autre membre. 25% de réussite. Cooldown : 24h."
    )
    @app_commands.describe(cible="Membre dont tu veux voler le Reiatsu")
    async def reiatsuvol_slash(self, interaction: discord.Interaction, cible: discord.Member):
        if cible is None:
            await interaction.response.send_message("ℹ️ Tu dois sélectionner un membre valide.", ephemeral=True)
            return
        await self._voler_reiatsu(interaction.user, cible, interaction)

    # ─────────────── Setup slash commands ───────────────
    async def cog_load(self):
        self.bot.tree.add_command(self.reiatsuvol_slash)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuVol(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
