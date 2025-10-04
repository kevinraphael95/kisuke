# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu_profil.py — Commande interactive /reiatsuprofil et !reiatsuprofil
# Objectif : Affiche le profil Reiatsu personnel d’un joueur (classe, compétences, cooldowns)
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
import time
import json
import os
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Tables utilisées
# ────────────────────────────────────────────────────────────────────────────────
TABLES = {
    "reiatsu": {
        "description": "Contient les informations personnelles Reiatsu de chaque joueur : score, classe, bonus et cooldowns.",
        "colonnes": {
            "user_id": "BIGINT — Identifiant Discord unique du joueur (clé primaire)",
            "username": "TEXT — Nom d'utilisateur au moment de la dernière mise à jour",
            "points": "INTEGER — Quantité actuelle de Reiatsu",
            "bonus5": "INTEGER — Bonus supplémentaire éventuel",
            "classe": "TEXT — Classe Reiatsu choisie par le joueur",
            "last_steal_attempt": "TIMESTAMP — Dernière tentative de vol",
            "steal_cd": "INTEGER — Cooldown du vol (en heures)",
            "last_skilled_at": "TIMESTAMP — Dernière utilisation de skill",
            "active_skill": "BOOLEAN — Si le skill est actif ou non"
        }
    }
}

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des classes depuis JSON
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
# 🧠 Cog principal — Reiatsu Profil
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuProfilCommand(commands.Cog):
    """Commande /reiatsuprofil et !reiatsuprofil — Affiche le profil personnel Reiatsu d’un joueur"""
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

    async def _send_profil(self, channel_or_interaction, author, target_user):
        user = target_user or author
        user_id = int(user.id)

        # Récupération des données utilisateur
        try:
            res = supabase.table("reiatsu").select(
                "username, points, bonus5, classe, last_steal_attempt, steal_cd, last_skilled_at, active_skill"
            ).eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[ERREUR DB] Lecture Reiatsu échouée : {e}")
            return await safe_send(channel_or_interaction, "❌ Erreur lors de la récupération de ton profil.")

        data = res.data[0] if res.data else {}
        if not data:
            return await safe_send(channel_or_interaction, "⚠️ Aucun profil Reiatsu trouvé. Utilise `!classe` pour commencer ton parcours.")

        # Extraction des champs
        points = data.get("points", 0)
        classe_nom = data.get("classe", "Aucune")
        bonus = data.get("bonus5", 0)
        last_steal = data.get("last_steal_attempt")
        steal_cd = data.get("steal_cd")
        last_skill = data.get("last_skilled_at")
        active_skill = data.get("active_skill", False)

        # Chargement classes.json
        CLASSES = load_classes()
        classe_data = CLASSES.get(classe_nom, None)

        # ────────────────────────────────────────────────────────────────────────
        # Formatage des sections du profil
        # ────────────────────────────────────────────────────────────────────────
        # Cooldown du vol
        cooldown_vol = "✅ Disponible"
        if last_steal and steal_cd:
            try:
                last_steal_dt = parser.parse(last_steal)
                if not last_steal_dt.tzinfo:
                    last_steal_dt = last_steal_dt.replace(tzinfo=timezone.utc)
                next_cd = last_steal_dt + timedelta(hours=steal_cd)
                now_dt = datetime.now(timezone.utc)
                if now_dt < next_cd:
                    restant = next_cd - now_dt
                    h, m = divmod(int(restant.total_seconds() // 60), 60)
                    cooldown_vol = f"⏳ {restant.days}j {h}h{m}m" if restant.days else f"⏳ {h}h{m}m"
            except Exception as e:
                print(f"[WARN] CD vol parsing : {e}")

        # Cooldown du skill
        cooldown_skill = "✅ Disponible"
        if last_skill:
            try:
                last_skill_dt = parser.parse(last_skill)
                if not last_skill_dt.tzinfo:
                    last_skill_dt = last_skill_dt.replace(tzinfo=timezone.utc)
                base_cd = 8 if classe_nom == "Illusionniste" else 12
                next_skill = last_skill_dt + timedelta(hours=base_cd)
                now_dt = datetime.now(timezone.utc)
                if now_dt < next_skill:
                    restant = next_skill - now_dt
                    h, m = divmod(int(restant.total_seconds() // 60), 60)
                    cooldown_skill = f"⏳ {restant.days}j {h}h{m}m" if restant.days else f"⏳ {h}h{m}m"
            except Exception as e:
                print(f"[WARN] CD skill parsing : {e}")
        if active_skill:
            cooldown_skill = "🌀 En cours d'utilisation"

        # ────────────────────────────────────────────────────────────────────────
        # Création de l'embed
        # ────────────────────────────────────────────────────────────────────────
        embed = discord.Embed(
            title=f"🎴 Profil Reiatsu de {user.display_name}",
            description="> *L’énergie spirituelle circule en toi...*",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="💠 Statistiques",
            value=(
                f"**Reiatsu :** {points}\n"
                f"**Classe :** {classe_nom}\n"
                f"**Bonus :** +{bonus}% Reiatsu"
            ),
            inline=False
        )

        if classe_data:
            embed.add_field(
                name="⚔️ Compétences",
                value=(
                    f"**Passive :** {classe_data['Passive']}\n"
                    f"**Active :** {classe_data['Active']}"
                ),
                inline=False
            )

        embed.add_field(
            name="⏳ Cooldowns",
            value=(
                f"**Vol :** {cooldown_vol}\n"
                f"**Skill :** {cooldown_skill}"
            ),
            inline=False
        )

        embed.set_footer(text="Utilise /classe pour changer de voie ou /skill pour activer ton pouvoir.")

        if isinstance(channel_or_interaction, discord.Interaction):
            await channel_or_interaction.response.send_message(embed=embed)
        else:
            await safe_send(channel_or_interaction, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="reiatsuprofil", description="💠 Affiche ton profil Reiatsu détaillé.")
    @app_commands.describe(member="Voir le profil Reiatsu d’un autre joueur")
    async def slash_profil(self, interaction: discord.Interaction, member: discord.Member = None):
        remaining = await self._check_cooldown(interaction.user.id)
        if remaining > 0:
            return await safe_respond(interaction, f"⏳ Attends encore {remaining:.1f}s.", ephemeral=True)
        await self._send_profil(interaction, interaction.user, member)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="reiatsuprofil", aliases=["rtsp", "rts profil"], help="💠 Affiche ton profil Reiatsu détaillé.")
    async def prefix_profil(self, ctx: commands.Context, member: discord.Member = None):
        remaining = await self._check_cooldown(ctx.author.id)
        if remaining > 0:
            return await safe_send(ctx.channel, f"⏳ Attends encore {remaining:.1f}s.")
        await self._send_profil(ctx.channel, ctx.author, member)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuProfilCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)





