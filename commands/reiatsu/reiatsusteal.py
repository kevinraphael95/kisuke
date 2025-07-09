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
from supabase_client import supabase  # ⚠️ Remplace par ton instance Supabase
import random

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class VolReiatsu(commands.Cog):
    """
    Commande !volreiatsu — Tente de voler du Reiatsu à un autre joueur (25% de chance)
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="volreiatsu",
        aliases=["stealreiatsu", "rtss", "rtsvol", "rtsv"],
        help="💠 Tente de voler 5% du Reiatsu d’un autre membre. 25% de réussite. Cooldown : 24h.",
        description="Commande de vol de Reiatsu avec échec possible. Perte de Reiatsu en cas d’échec. Cooldown persistant."
    )
    async def volreiatsu(self, ctx: commands.Context, cible: discord.Member = None):        
        """Commande principale pour voler du Reiatsu à un autre membre."""

        voleur = ctx.author

        if cible is None:
            voleur_id = str(voleur.id)
            voleur_data = supabase.table("reiatsu").select("*").eq("user_id", voleur_id).execute()
            now = datetime.utcnow()
            dernier_vol_str = voleur_data.data[0].get("last_steal_attempt") if voleur_data.data else None

            if dernier_vol_str:
                dernier_vol = datetime.fromisoformat(dernier_vol_str)
                prochain_vol = dernier_vol + timedelta(hours=24)
                if now < prochain_vol:
                    restant = prochain_vol - now
                    h, m = divmod(restant.seconds // 60, 60)
                    await ctx.send(f"⏳ Il te reste **{restant.days}j {h}h{m}m** avant de pouvoir retenter un vol.")
                    return
            await ctx.send("ℹ️ Tu peux utiliser la commande `!volreiatsu @membre` pour tenter de voler du Reiatsu.")
            return




        

        # ❌ Auto-ciblage interdit
        if voleur.id == cible.id:
            await ctx.send("❌ Tu ne peux pas te voler toi-même.")
            return

        voleur_id = str(voleur.id)
        cible_id = str(cible.id)

        # 📥 Récupération des données Supabase
        voleur_data = supabase.table("reiatsu").select("*").eq("user_id", voleur_id).execute()
        cible_data = supabase.table("reiatsu").select("*").eq("user_id", cible_id).execute()

        voleur_points = voleur_data.data[0]["points"] if voleur_data.data else 0
        cible_points = cible_data.data[0]["points"] if cible_data.data else 0

        # ⏳ Vérifie cooldown
        now = datetime.utcnow()
        dernier_vol_str = voleur_data.data[0].get("last_steal_attempt") if voleur_data.data else None

        if dernier_vol_str:
            dernier_vol = datetime.fromisoformat(dernier_vol_str)
            prochain_vol = dernier_vol + timedelta(hours=24)
            if now < prochain_vol:
                restant = prochain_vol - now
                h, m = divmod(restant.seconds // 60, 60)
                await ctx.send(f"⏳ Tu dois encore attendre **{restant.days}j {h}h{m}m** avant de retenter.")
                return

        # 🛑 Vérifie que la cible et le voleur ont des points
        if cible_points == 0:
            await ctx.send(f"⚠️ {cible.mention} n’a pas de Reiatsu à voler.")
            return

        if voleur_points == 0:
            await ctx.send("⚠️ Tu dois avoir au moins **1 point** de Reiatsu pour tenter un vol.")
            return

        # 🎲 Calcul du vol
        montant = max(1, cible_points // 20)
        succes = random.random() < 0.25

        # 🛠️ Préparation de la mise à jour Supabase
        payload_voleur = {
            "last_steal_attempt": now.isoformat()
        }

        if succes:
            # ✅ Vol réussi
            payload_voleur["points"] = voleur_points + montant
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()

            supabase.table("reiatsu").update({
                "points": max(0, cible_points - montant)
            }).eq("user_id", cible_id).execute()

            await ctx.send(f"🩸 {voleur.mention} a réussi à voler **{montant}** points de Reiatsu à {cible.mention} !")



        else:
            # ❌ Vol raté → perte pour le voleur
            payload_voleur["points"] = max(0, voleur_points - montant)
            supabase.table("reiatsu").update(payload_voleur).eq("user_id", voleur_id).execute()

            # ➕ Le bot récupère les points perdus
            bot_id = str(self.bot.user.id)
            bot_data = supabase.table("reiatsu").select("id, points").eq("user_id", bot_id).execute()

            if bot_data.data:
                points_actuels = bot_data.data[0]["points"]
                supabase.table("reiatsu").update({"points": points_actuels + montant}).eq("user_id", bot_id).execute()
            else:
                supabase.table("reiatsu").insert({
                    "user_id": bot_id,
                    "username": self.bot.user.name,
                    "points": montant
                }).execute()

            await ctx.send(f"😵 {voleur.mention} a tenté de voler {cible.mention}... mais a échoué et perdu **{montant}** points ! Ces points vont au bot. �
            �")

        
# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = VolReiatsu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
