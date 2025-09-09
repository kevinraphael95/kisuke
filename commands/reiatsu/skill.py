# ────────────────────────────────────────────────────────────────────────────────
# 📌 skill.py — Commande interactive /skill et !skill
# Objectif : Utiliser la compétence active de la classe du joueur avec cooldown
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import random
from datetime import datetime, timezone, timedelta
import discord
from discord.ext import commands
from utils.supabase_utils import supabase
from discord_utils import safe_send

# Cooldowns (heures → secondes)
CLASS_CD = {
    "Travailleur": 0,
    "Voleur": 12 * 3600,
    "Absorbeur": 12 * 3600,
    "Illusionniste": 8 * 3600,
    "Parieur": 12 * 3600
}

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Cog Skill
# ────────────────────────────────────────────────────────────────────────────────
class Skill(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ──────────────────────────────
    # ⚡ Commande !skill
    # ──────────────────────────────
    @commands.command(name="skill")
    async def skill_command(self, ctx):
        """
        Active la compétence spécifique de la classe du joueur avec cooldown.
        """
        user_id = str(ctx.author.id)

        # ──────────────────────────────
        # 📌 Récupération des infos joueur
        # ──────────────────────────────
        response = supabase.table("reiatsu").select("*").eq("user_id", user_id).single().execute()
        data = getattr(response, "data", None)
        if not data:
            return await safe_send(ctx, "❌ Tu n'as pas encore commencé l'aventure. Utilise `!start`.")

        classe = data.get("classe", "Travailleur")
        reiatsu = data.get("points", 0)
        last_skill = data.get("last_skill")
        skill_cd = data.get("skill_cd", 0)

        now = datetime.now(timezone.utc)

        # ──────────────────────────────
        # ⏳ Vérif cooldown
        # ──────────────────────────────
        if last_skill:
            elapsed = (now - datetime.fromisoformat(last_skill)).total_seconds()
            if elapsed < skill_cd:
                remaining = timedelta(seconds=int(skill_cd - elapsed))
                return await safe_send(ctx, f"⏳ Compétence encore en recharge ! Temps restant : **{remaining}**")

        # ──────────────────────────────
        # 🔹 Gestion des compétences par classe
        # ──────────────────────────────
        updated_fields = {}
        result_message = ""

        # ─ Travailleur ─
        if classe == "Travailleur":
            result_message = "💼 Tu es Travailleur : pas de compétence active."
            new_cd = 0

        # ─ Voleur ─
        elif classe == "Voleur":
            updated_fields["vol_garanti"] = True
            result_message = "🥷 Ton prochain vol sera garanti."
            new_cd = CLASS_CD["Voleur"]

        # ─ Absorbeur ─
        elif classe == "Absorbeur":
            updated_fields["prochain_reiatsu"] = 100
            result_message = "🌀 Ton prochain Reiatsu absorbé sera un Super Reiatsu (100 points)."
            new_cd = CLASS_CD["Absorbeur"]

        # ─ Illusionniste ─
        elif classe == "Illusionniste":
            if data.get("faux_reiatsu_active", False):
                return await safe_send(ctx, "❌ Tu as déjà un faux Reiatsu actif.")

            supabase.table("reiatsu_spawn").insert({
                "user_id": user_id,
                "type": "faux",
                "points": 0,
                "created_at": now.isoformat()
            }).execute()

            updated_fields["faux_reiatsu_active"] = True
            result_message = "🎭 Tu as créé un faux Reiatsu ! Si quelqu’un le prend → tu gagnes 10."
            new_cd = CLASS_CD["Illusionniste"]

        # ─ Parieur ─
        elif classe == "Parieur":
            if reiatsu < 10:
                return await safe_send(ctx, "❌ Tu n'as pas assez de Reiatsu pour parier (10 requis).")

            new_points = reiatsu - 10
            if random.random() < 0.5:
                new_points += 30
                result_message = "🎲 Tu as misé 10 Reiatsu et gagné 30 !"
            else:
                result_message = "🎲 Tu as misé 10 Reiatsu et perdu."
            updated_fields["points"] = new_points
            new_cd = CLASS_CD["Parieur"]

        # ──────────────────────────────
        # 🔹 Mise à jour en base
        # ──────────────────────────────
        updated_fields["last_skill"] = now.isoformat()
        updated_fields["skill_cd"] = new_cd
        supabase.table("reiatsu").update(updated_fields).eq("user_id", user_id).execute()

        # ──────────────────────────────
        # 🔹 Envoi du résultat
        # ──────────────────────────────
        await safe_send(ctx, result_message)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Skill(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
