# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsuprofil.py — Commande interactive /reiatsuprofil et !reiatsuprofil
# Objectif : Affiche le profil Reiatsu d’un joueur (classe, compétences, cooldowns)
# Catégorie : Reiatsu
# Accès : Tous
# Cooldown : 5 secondes
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from dateutil import parser
from datetime import datetime, timedelta, timezone
import os
import json
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

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
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuProfil(commands.Cog):
    """Commande /reiatsuprofil et !reiatsuprofil — Affiche le profil personnel Reiatsu d’un joueur"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_profil(self, channel_or_interaction, author, target_user):
        user = target_user or author
        user_id = int(user.id)

        # Récupération des données Reiatsu
        try:
            res = supabase.table("reiatsu").select(
                "username, points, bonus5, classe, last_steal_attempt, steal_cd, last_skilled_at, active_skill"
            ).eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[ERREUR DB] Lecture Reiatsu échouée : {e}")
            return await safe_send(channel_or_interaction, "❌ Impossible de récupérer ton profil.")

        data = res.data[0] if res.data else {}
        if not data:
            return await safe_send(channel_or_interaction, "⚠️ Aucun profil trouvé. Utilise `!classe` pour commencer.")

        points = data.get("points", 0)
        classe_nom = data.get("classe", None)
        bonus = data.get("bonus5", 0)
        last_steal = data.get("last_steal_attempt")
        steal_cd = data.get("steal_cd")
        last_skill = data.get("last_skilled_at")
        active_skill = data.get("active_skill", False)

        CLASSES = load_classes()
        classe_data = CLASSES.get(classe_nom) if classe_nom else None

        # Cooldowns formatés
        cooldown_vol = "✅ Disponible"
        if last_steal and steal_cd:
            try:
                last_dt = parser.parse(last_steal)
                if not last_dt.tzinfo: last_dt = last_dt.replace(tzinfo=timezone.utc)
                next_cd = last_dt + timedelta(hours=steal_cd)
                now_dt = datetime.now(timezone.utc)
                if now_dt < next_cd:
                    restant = next_cd - now_dt
                    h, m = divmod(int(restant.total_seconds() // 60), 60)
                    cooldown_vol = f"⏳ {restant.days}j {h}h{m}m" if restant.days else f"⏳ {h}h{m}m"
            except: pass

        cooldown_skill = "✅ Disponible"
        if last_skill:
            try:
                last_dt = parser.parse(last_skill)
                if not last_dt.tzinfo: last_dt = last_dt.replace(tzinfo=timezone.utc)
                base_cd = 8 if classe_nom == "Illusionniste" else 12
                next_cd = last_dt + timedelta(hours=base_cd)
                now_dt = datetime.now(timezone.utc)
                if now_dt < next_cd:
                    restant = next_cd - now_dt
                    h, m = divmod(int(restant.total_seconds() // 60), 60)
                    cooldown_skill = f"⏳ {restant.days}j {h}h{m}m" if restant.days else f"⏳ {h}h{m}m"
            except: pass
        if active_skill: cooldown_skill = "🌀 En cours"

        # Embed profil
        embed = discord.Embed(
            title=f"🎴 Profil Reiatsu de {user.display_name}",
            description="> *L’énergie spirituelle circule en toi...*",
            color=discord.Color.purple()
        )

        # Statistiques
        embed.add_field(
            name="💠 Statistiques",
            value=f"**Reiatsu :** {points}\n**Bonus :** +{bonus}%",
            inline=False
        )

        # Classe
        if classe_data:
            embed.add_field(
                name="🏷️ Classe",
                value=f"{classe_nom}\n• Passif : {classe_data['Passive']}\n• Skill : {classe_data['Active']}",
                inline=False
            )
        else:
            embed.add_field(
                name="🏷️ Classe",
                value="Aucune classe choisie\n`!!classe` pour choisir une classe",
                inline=False
            )

        # Cooldowns
        embed.add_field(
            name="⏳ Cooldowns",
            value=f"**Vol :** {cooldown_vol}\n**Skill :** {cooldown_skill}",
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
    @app_commands.checks.cooldown(rate=1, per=5.0, key=lambda i: i.user.id)
    async def slash_profil(self, interaction: discord.Interaction, member: discord.Member = None):
        await self._send_profil(interaction, interaction.user, member)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="reiatsuprofil", aliases=["rtsp", "rts profil"], help="💠 Affiche ton profil Reiatsu détaillé.")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_profil(self, ctx: commands.Context, member: discord.Member = None):
        await self._send_profil(ctx.channel, ctx.author, member)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuProfil(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)

