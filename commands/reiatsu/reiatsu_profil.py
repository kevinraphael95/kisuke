# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu_profil.py — Commande interactive /reiatsuprofil et !reiatsuprofil
# Objectif : Affiche le profil complet d’un joueur : score, classe, skills et cooldowns
# Catégorie : Reiatsu
# Accès : Public
# Cooldown : 1 utilisation / 3 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from dateutil import parser
from datetime import datetime, timedelta, timezone
import json
import time
import os
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Tables utilisées
# ────────────────────────────────────────────────────────────────────────────────
TABLES = {
    "reiatsu": {
        "description": "Table principale contenant les informations Reiatsu personnelles de chaque joueur.",
        "columns": {
            "user_id": "BIGINT — Identifiant Discord unique de l'utilisateur (clé primaire)",
            "username": "TEXT — Nom d'utilisateur actuel",
            "points": "INTEGER — Score de Reiatsu actuel",
            "bonus5": "INTEGER — Bonus éventuel appliqué",
            "classe": "TEXT — Classe Reiatsu choisie par le joueur",
            "steal_cd": "INTEGER — Cooldown du vol en heures",
            "last_steal_attempt": "TIMESTAMP — Dernière tentative de vol",
            "last_skilled_at": "TIMESTAMP — Dernière utilisation du skill",
            "active_skill": "BOOLEAN — Indique si le skill est actuellement actif",
            "fake_spawn_id": "TEXT — ID de spawn temporaire (optionnel)"
        }
    }
}

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des classes Reiatsu
# ────────────────────────────────────────────────────────────────────────────────
CLASSES_JSON_PATH = os.path.join("data", "classes.json")

def load_classes():
    try:
        with open(CLASSES_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {CLASSES_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuProfil(commands.Cog):
    """Commande /reiatsuprofil et !reiatsuprofil — Affiche le profil Reiatsu complet d’un joueur"""

    COOLDOWN = 3

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_cooldowns = {}

    async def _check_cooldown(self, user_id: int):
        now = time.time()
        last = self.user_cooldowns.get(user_id, 0)
        if now - last < self.COOLDOWN:
            return self.COOLDOWN - (now - last)
        self.user_cooldowns[user_id] = now
        return 0

    async def _send_profile(self, channel_or_interaction, author, target_user):
        user = target_user or author
        user_id = int(user.id)

        # 📥 Récupération des données depuis Supabase
        try:
            data = supabase.table("reiatsu").select("*").eq("user_id", user_id).execute().data
        except Exception as e:
            print(f"[ERREUR DB] Impossible de récupérer le profil Reiatsu : {e}")
            return await safe_send(channel_or_interaction, "❌ Erreur lors de la récupération du profil Reiatsu.")
        user_data = data[0] if data else {}

        # Champs
        points = user_data.get("points", 0)
        classe_nom = user_data.get("classe")
        bonus = user_data.get("bonus5", 0)
        last_steal_str = user_data.get("last_steal_attempt")
        steal_cd = user_data.get("steal_cd", 24)
        last_skill_str = user_data.get("last_skilled_at")
        active_skill = user_data.get("active_skill", False)

        # Chargement des classes
        CLASSES = load_classes()
        classe_text = "Aucune classe sélectionnée. Utilise `!classe` pour en choisir une."
        if classe_nom and classe_nom in CLASSES:
            c = CLASSES[classe_nom]
            classe_text = (
                f"🏷️ Classe : **{classe_nom}**\n"
                f"🌙 Passive : {c.get('Passive', 'Aucune')}\n"
                f"⚡ Active : {c.get('Active', 'Aucune')}"
            )

        # Cooldown de vol
        cooldown_text = "Disponible ✅"
        if last_steal_str and steal_cd:
            try:
                last_steal = parser.parse(last_steal_str).astimezone(timezone.utc)
                next_steal = last_steal + timedelta(hours=steal_cd)
                now_dt = datetime.now(timezone.utc)
                if now_dt < next_steal:
                    restant = next_steal - now_dt
                    h, m = divmod(int(restant.total_seconds() // 60), 60)
                    cooldown_text = f"{restant.days}j {h}h{m}m" if restant.days else f"{h}h{m}m"
            except Exception:
                pass

        # Cooldown skill
        skill_text = "Disponible ✅"
        if last_skill_str:
            try:
                last_skill = parser.parse(last_skill_str).astimezone(timezone.utc)
                base_cd = 8 if classe_nom == "Illusionniste" else 12
                next_skill = last_skill + timedelta(hours=base_cd)
                now_dt = datetime.now(timezone.utc)
                if now_dt < next_skill:
                    restant = next_skill - now_dt
                    h, m = divmod(int(restant.total_seconds() // 60), 60)
                    skill_text = f"{restant.days}j {h}h{m}m" if restant.days else f"{h}h{m}m"
            except Exception:
                pass
        if active_skill:
            skill_text = "⏳ En cours d'utilisation"

        # 📊 Embed
        embed = discord.Embed(
            title=f"__Profil Reiatsu de {user.display_name}__",
            description=(
                f"💠 **Reiatsu** : {points} (+{bonus} bonus)\n"
                f"🔄 **Cooldown vol** : {cooldown_text}\n"
                f"⚡ **Skill** : {skill_text}\n\n"
                f"{classe_text}\n\n"
                f"`!!rtsv <@utilisateur>` pour voler du Reiatsu\n"
                f"`!!classe` pour changer de classe\n"
                f"`!!skill` pour activer ton skill"
            ),
            color=discord.Color.purple()
        )
        embed.set_footer(text="💠 Commande /reiatsuprofil ou !reiatsuprofil pour voir ton profil.")

        if isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.send_message(embed=embed)
        else:
            await safe_send(channel_or_interaction, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commandes SLASH + PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="reiatsuprofil", description="💠 Affiche ton profil Reiatsu complet (ou celui d’un autre membre).")
    @app_commands.describe(member="Membre dont tu veux voir le profil Reiatsu")
    async def slash_reiatsuprofil(self, interaction: discord.Interaction, member: discord.Member = None):
        remaining = await self._check_cooldown(interaction.user.id)
        if remaining > 0:
            return await safe_respond(interaction, f"⏳ Attends encore {remaining:.1f}s.", ephemeral=True)
        await self._send_profile(interaction, interaction.user, member)

    @commands.command(
        name="reiatsuprofil",
        aliases=["rtsp", "rtsprofil", "rts_profil"],
        help="💠 Affiche ton profil Reiatsu complet (ou celui d’un autre membre)."
    )
    async def prefix_reiatsuprofil(self, ctx: commands.Context, member: discord.Member = None):
        remaining = await self._check_cooldown(ctx.author.id)
        if remaining > 0:
            return await safe_send(ctx.channel, f"⏳ Attends encore {remaining:.1f}s.")
        await self._send_profile(ctx.channel, ctx.author, member)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuProfil(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
