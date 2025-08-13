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
from datetime import datetime, timezone
import discord
from discord.ext import commands
from utils.supabase_utils import supabase
from discord_utils import safe_send

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
        Active la compétence spécifique de la classe du joueur.
        """

        user_id = str(ctx.author.id)

        # ──────────────────────────────
        # 📌 Récupération des infos joueur
        # ──────────────────────────────
        data = supabase.table("reiatsu").select("*").eq("user_id", user_id).single().execute().data
        if not data:
            return await safe_send(ctx, "❌ Tu n'as pas encore commencé l'aventure. Utilise `!start`.")

        classe = data.get("classe", "Travailleur")
        reiatsu = data.get("points", 0)
        result_message = ""
        updated_fields = {}

        # ──────────────────────────────
        # 🔹 Gestion des compétences par classe
        # ──────────────────────────────

        # ─ Travailleur ─
        if classe == "Travailleur":
            result_message = "💼 Tu es Travailleur : pas de compétence active."

        # ─ Voleur ─
        elif classe == "Voleur":
            updated_fields["vol_garanti"] = True
            result_message = "🗝️ Ton prochain vol sera garanti."

        # ─ Absorbeur ─
        elif classe == "Absorbeur":
            updated_fields["prochain_reiatsu"] = 100
            result_message = "⚡ Ton prochain Reiatsu absorbé sera un Super Reiatsu (100 points) garanti."

        # ─ Illusionniste ─
        elif classe == "Illusionniste":
            if data.get("faux_reiatsu_active"):
                return await safe_send(ctx, "❌ Tu as déjà un faux Reiatsu actif.")

            # Création du faux Reiatsu
            fake_reiatsu_data = {
                "user_id": user_id,
                "type": "faux",
                "points": 0,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            supabase.table("reiatsu_spawn").insert(fake_reiatsu_data).execute()

            updated_fields["faux_reiatsu_active"] = True
            result_message = (
                "🎭 Tu as créé un faux Reiatsu ! "
                "Si quelqu’un le prend, tu gagnes 10 points."
            )

        # ─ Parieur ─
        elif classe == "Parieur":
            if reiatsu < 10:
                return await safe_send(ctx, "❌ Tu n'as pas assez de Reiatsu pour parier (10 requis).")

            new_points = reiatsu - 10
            if random.random() < 0.5:
                new_points += 30
                result_message = "🎰 Tu as misé 10 Reiatsu et gagné 30 !"
            else:
                result_message = "🎰 Tu as misé 10 Reiatsu et perdu."
            updated_fields["points"] = new_points

        # ──────────────────────────────
        # 🔹 Mise à jour en base
        # ──────────────────────────────
        updated_fields["comp_cd"] = datetime.now(timezone.utc).isoformat()
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
