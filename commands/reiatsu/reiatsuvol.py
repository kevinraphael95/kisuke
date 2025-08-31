# ────────────────────────────────────────────────────────────────────────────────
# 📌 volreiatsu.py — Commande interactive !volreiatsu
# Objectif : Permet de voler 5% du Reiatsu d’un autre joueur avec 25% de réussite.
# Catégorie : VAACT
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from utils.supabase_client import supabase
import random

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuVol(commands.Cog):
    """
    Commande !volreiatsu — Tente de voler du Reiatsu à un autre joueur (25% de chance)
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="reiatsuvol",
        aliases=["rtsv", "volreiatsu", "vrts"],
        help="💠 Tente de voler 10% du Reiatsu d’un autre membre. 25% de réussite. Cooldown : 24h.",
        description="Commande de vol de Reiatsu avec échec possible. Pas de perte de Reiatsu en cas d’échec. Cooldown persistant."
    )
    async def volreiatsu(self, ctx: commands.Context, cible: discord.Member = None):
        voleur = ctx.author
        voleur_id = str(voleur.id)

        # Récupération des données du voleur (nécessaire pour cooldown)
        voleur_data = supabase.table("reiatsu").select("*").eq("user_id", voleur_id).execute()
        if not voleur_data.data:
            await ctx.send("⚠️ Données introuvables pour toi.")
            return
        voleur_data = voleur_data.data[0]

        voleur_classe = voleur_data.get("classe")
        voleur_cd = voleur_data.get("steal_cd", 24)
        now = datetime.utcnow()
        dernier_vol_str = voleur_data.get("last_steal_attempt")

        if dernier_vol_str:
            dernier_vol = datetime.fromisoformat(dernier_vol_str)
            prochain_vol = dernier_vol + timedelta(hours=voleur_cd)
            if now < prochain_vol:
                restant = prochain_vol - now
                j = restant.days
                h, m = divmod(restant.seconds // 60, 60)
                await ctx.send(f"⏳ Tu dois encore attendre **{j}j {h}h{m}m** avant de retenter.")
                return

        # Ici cooldown OK => on vérifie la cible
        if cible is None:
            await ctx.send("ℹ️ Tu dois faire `!!volreiatsu @membre` pour tenter de voler du Reiatsu.")
            return
        if voleur.id == cible.id:
            await ctx.send("❌ Tu ne peux pas te voler toi-même.")
            return

        cible_id = str(cible.id)

        # 📥 Récupération des données Supabase
        cible_data = supabase.table("reiatsu").select("*").eq("user_id", cible_id).execute()
        if not cible_data.data:
            await ctx.send("⚠️ Données introuvables pour la cible.")
            return
        cible_data = cible_data.data[0]

        voleur_points = voleur_data.get("points", 0)
        cible_points = cible_data.get("points", 0)
        cible_classe = cible_data.get("classe")

        if cible_points == 0:
            await ctx.send(f"⚠️ {cible.mention} n’a pas de Reiatsu à voler.")
            return
        if voleur_points == 0:
            await ctx.send("⚠️ Tu dois avoir au moins **1 point** de Reiatsu pour tenter un vol.")
            return

        # 🎲 Calcul du vol
        montant = max(1, cible_points // 10)  # 10%
        if voleur_classe == "Voleur" and random.random() < 0.15:  # 15% de chance de doubler le gain
            montant *= 2

        if voleur_classe == "Voleur":
            succes = random.random() < 0.67  # 67% de chance pour la classe Voleur
        else:
            succes = random.random() < 0.25  # 25% sinon


        # Préparation du payload pour le voleur (update cooldown et éventuellement points)
        payload_voleur = {
            "last_steal_attempt": now.isoformat()
        }

        if succes:
            # Succès : ajout des points au voleur
            payload_voleur["points"] = voleur_points + montant
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()

            if cible_classe == "Illusionniste" and random.random() < 0.5:
                await ctx.send(f"🩸 {voleur.mention} a volé **{montant}** points à {cible.mention}... mais c'était une illusion, {cible.mention} n'a rien perdu !")
            else:
                supabase.table("reiatsu").update({
                    "points": max(0, cible_points - montant)
                }).eq("user_id", cible_id).execute()
                await ctx.send(f"🩸 {voleur.mention} a réussi à voler **{montant}** points de Reiatsu à {cible.mention} !")

        else:
            # Échec : seulement mise à jour du cooldown, pas de perte de points ni de transfert au bot
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()
            await ctx.send(f"😵 {voleur.mention} a tenté de voler {cible.mention}... mais a échoué !")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuVol(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
