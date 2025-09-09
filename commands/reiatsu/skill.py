# ────────────────────────────────────────────────────────────────────────────────
# 📌 skill.py — Commande simple /skill et !skill
# Objectif : Utiliser la compétence active de la classe du joueur avec cooldown
# Catégorie : Reiatsu
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur (préfixe & slash)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import random
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from utils.supabase_utils import supabase
from utils.discord_utils import safe_send, safe_followup  # pour defer et followup

# Cooldowns par classe (heures → secondes)
CLASS_CD = {
    "Travailleur": 0,
    "Voleur": 12 * 3600,
    "Absorbeur": 12 * 3600,
    "Illusionniste": 8 * 3600,
    "Parieur": 12 * 3600
}

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Skill(commands.Cog):
    """Commande /skill et !skill — Active la compétence spécifique de la classe du joueur avec cooldown"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("[COG LOAD] Skill cog chargé ✅")

    # 🔹 Fonction interne commune pour l'exécution
    async def _execute_skill(self, user_id: str):
        try:
            response = supabase.table("reiatsu").select("*").eq("user_id", user_id).single().execute()
            data = getattr(response, "data", None)
        except Exception as e:
            print(f"[ERREUR SUPABASE] {e}")
            return "❌ Impossible de récupérer les données."

        if not data:
            return "❌ Tu n'as pas encore commencé l'aventure. Utilise `!start`."

        classe = data.get("classe", "Travailleur")
        reiatsu = data.get("points", 0)
        last_skill = data.get("last_skill")
        skill_cd = data.get("skill_cd", 0)
        active_skill = data.get("active_skill")
        now = datetime.now(timezone.utc)

        # ⏳ Vérification du cooldown
        if last_skill:
            elapsed = (now - datetime.fromisoformat(last_skill)).total_seconds()
            if elapsed < skill_cd:
                remaining = timedelta(seconds=int(skill_cd - elapsed))
                return f"⏳ Compétence encore en recharge ! Temps restant : **{remaining}**"

        # 🔹 Gestion des compétences par classe
        updated_fields = {}
        result_message = ""

        if classe == "Travailleur":
            result_message = "💼 Tu es Travailleur : pas de compétence active."
            new_cd = 0
        elif classe == "Voleur":
            updated_fields["vol_garanti"] = True
            result_message = "🥷 Ton prochain vol sera garanti."
            new_cd = CLASS_CD["Voleur"]
        elif classe == "Absorbeur":
            updated_fields["prochain_reiatsu"] = 100
            result_message = "🌀 Ton prochain Reiatsu absorbé sera un Super Reiatsu (100 points)."
            new_cd = CLASS_CD["Absorbeur"]
        elif classe == "Illusionniste":
            if active_skill and isinstance(active_skill, dict) and active_skill.get("type") == "faux":
                return "❌ Tu as déjà un faux Reiatsu actif."
            updated_fields["active_skill"] = {
                "type": "faux",
                "owner_id": user_id,
                "points": 0,
                "created_at": now.isoformat()
            }
            result_message = "🎭 Tu as créé un faux Reiatsu ! Si quelqu’un le prend → tu gagnes 10."
            new_cd = CLASS_CD["Illusionniste"]
        elif classe == "Parieur":
            if reiatsu < 10:
                return "❌ Tu n'as pas assez de Reiatsu pour parier (10 requis)."
            new_points = reiatsu - 10
            if random.random() < 0.5:
                new_points += 30
                result_message = "🎲 Tu as misé 10 Reiatsu et gagné 30 !"
            else:
                result_message = "🎲 Tu as misé 10 Reiatsu et perdu."
            updated_fields["points"] = new_points
            new_cd = CLASS_CD["Parieur"]

        # 🔹 Mise à jour en base
        updated_fields["last_skill"] = now.isoformat()
        updated_fields["skill_cd"] = new_cd
        try:
            supabase.table("reiatsu").update(updated_fields).eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[ERREUR SUPABASE UPDATE] {e}")
            return "❌ Impossible de mettre à jour les données."

        return result_message

    # 🔹 Commande SLASH
    @app_commands.command(
        name="skill",
        description="Active la compétence spécifique de ta classe avec cooldown."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_skill(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            message = await self._execute_skill(str(interaction.user.id))
            await safe_followup(interaction, message)
        except app_commands.CommandOnCooldown as e:
            await safe_followup(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /skill] {e}")
            await safe_followup(interaction, "❌ Une erreur est survenue.")

    # 🔹 Commande PREFIX
    @commands.command(name="skill")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_skill(self, ctx: commands.Context):
        try:
            message = await self._execute_skill(str(ctx.author.id))
            await safe_send(ctx.channel, message)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !skill] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Skill(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
    print("[COG SETUP] Skill cog ajouté ✅")

    # 🔹 Synchronisation des slash commands
    @bot.event
    async def on_ready():
        try:
            await bot.tree.sync()
            print("[SYNC SLASH] Slash commands synchronisées ✅")
        except Exception as e:
            print(f"[SYNC SLASH] {e}")
