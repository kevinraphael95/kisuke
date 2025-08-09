# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsuvol.py — Commande !reiatsuvol + /reiatsuvol avec logique commune
# Objectif : Permet de voler du Reiatsu à un autre membre (avec cooldown et chance)
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
from dateutil import parser
import random

from supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuVolCog(commands.Cog):
    """
    Commande !reiatsuvol et /reiatsuvol — Permet de voler du Reiatsu à un autre membre,
    avec cooldown et chance d'échec.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────────
    # Fonction interne commune : gestion du vol
    # ────────────────────────────────────────────────────────────────────────────────
    async def process_steal(self, ctx, author: discord.Member, target: discord.Member):
        """
        Logique commune pour voler du Reiatsu, utilisée par la commande préfixe et slash.
        """
        if target == author:
            await safe_respond(ctx, "❌ Tu ne peux pas te voler toi-même !")
            return

        user_id = str(author.id)
        cible_id = str(target.id)

        # Récupération données voleur
        voleur_resp = supabase.table("reiatsu") \
            .select("points, classe, last_steal_attempt, steal_cd") \
            .eq("user_id", user_id).execute()
        voleur = voleur_resp.data[0] if voleur_resp.data else None

        # Récupération données cible
        cible_resp = supabase.table("reiatsu") \
            .select("points") \
            .eq("user_id", cible_id).execute()
        cible_data = cible_resp.data[0] if cible_resp.data else None

        if voleur is None:
            await safe_respond(ctx, "❌ Tu n'as pas encore de points de Reiatsu. Commence à en gagner avant de voler !")
            return
        if cible_data is None:
            await safe_respond(ctx, f"❌ {target.display_name} n'a pas encore de points de Reiatsu.")
            return

        points_voleur = voleur.get("points", 0)
        points_cible = cible_data.get("points", 0)
        classe = voleur.get("classe")
        last_steal_str = voleur.get("last_steal_attempt")
        steal_cd = voleur.get("steal_cd")

        # Défaut cooldown selon classe si pas défini
        if steal_cd is None:
            if classe == "Voleur":
                steal_cd = 19
            else:
                steal_cd = 24
            supabase.table("reiatsu").update({"steal_cd": steal_cd}).eq("user_id", user_id).execute()

        # Calcul cooldown restant
        cooldown_restant = 0
        if last_steal_str:
            last_steal = parser.parse(last_steal_str)
            now = datetime.utcnow()
            fin_cooldown = last_steal + timedelta(hours=steal_cd)
            if now < fin_cooldown:
                cooldown_restant = (fin_cooldown - now).total_seconds()

        if cooldown_restant > 0:
            h, m = divmod(int(cooldown_restant // 60), 60)
            await safe_respond(ctx, f"⏳ Tu dois attendre encore **{h}h{m}m** avant de pouvoir voler à nouveau.")
            return

        if points_cible <= 0:
            await safe_respond(ctx, f"❌ {target.display_name} n’a aucun Reiatsu à te voler.")
            return

        # Chance succès (75%)
        if random.random() > 0.75:
            # Échec, mise à jour cooldown quand même
            supabase.table("reiatsu").update({"last_steal_attempt": datetime.utcnow().isoformat()}) \
                .eq("user_id", user_id).execute()
            await safe_respond(ctx, f"❌ Tentative de vol échouée contre {target.display_name} ! Sois plus prudent la prochaine fois.")
            return

        # Calcul Reiatsu volé (10% à 30%)
        vol_pts = max(1, int(points_cible * random.uniform(0.10, 0.30)))

        # Mise à jour en base
        new_points_voleur = points_voleur + vol_pts
        new_points_cible = points_cible - vol_pts

        supabase.table("reiatsu").update({
            "points": new_points_voleur,
            "last_steal_attempt": datetime.utcnow().isoformat()
        }).eq("user_id", user_id).execute()

        supabase.table("reiatsu").update({
            "points": new_points_cible
        }).eq("user_id", cible_id).execute()

        # Embed résultat
        embed = discord.Embed(
            title="💠 Vol de Reiatsu réussi !",
            description=(
                f"Tu as volé **{vol_pts}** points de Reiatsu à {target.display_name}.\n"
                f"• Ton nouveau total : **{new_points_voleur}** pts\n"
                f"• Total de {target.display_name} : **{new_points_cible}** pts\n\n"
                f"⏳ Cooldown vol : {steal_cd} heures"
            ),
            color=discord.Color.purple()
        )
        await safe_send(ctx.channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────────
    # Commande préfixe !reiatsuvol
    # ────────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="reiatsuvol",
        aliases=["rvol"],
        help="💠 Voler du Reiatsu à un membre (cooldown 20-24h selon classe).",
        description="Vol du Reiatsu à un autre membre avec chance d'échec et cooldown."
    )
    async def reiatsuvol(self, ctx: commands.Context, cible: discord.Member = None):
        if cible is None:
            await safe_respond(ctx, "❌ Tu dois mentionner un membre dont tu veux voler le Reiatsu.")
            return
        await self.process_steal(ctx, ctx.author, cible)

    # ────────────────
    # Commande slash /reiatsuvol
    # ────────────────
    @app_commands.command(
        name="reiatsuvol",
        description="Voler du Reiatsu à un membre (cooldown 20-24h selon classe)."
    )
    @app_commands.describe(membre="Membre dont tu veux voler le Reiatsu")
    async def slash_reiatsuvol(self, interaction: discord.Interaction, membre: discord.Member):
        await self.process_steal(interaction, interaction.user, membre)

    # ────────────────
    # Enregistrement de la commande slash dans le groupe
    # ────────────────
    @commands.Cog.listener()
    async def on_ready(self):
        # Ajout de la commande slash (si pas déjà ajoutée)
        try:
            self.bot.tree.add_command(self.slash_reiatsuvol)
            await self.bot.tree.sync()
        except Exception:
            pass

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuVolCog(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
