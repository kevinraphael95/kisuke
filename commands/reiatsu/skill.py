# ────────────────────────────────────────────────────────────────────────────────
# 📌 skill.py — Commande interactive /skill et !skill
# Objectif : Utiliser la compétence active de la classe du joueur avec cooldown
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View
import os
import json
from datetime import datetime, timedelta
from utils.discord_utils import safe_send, safe_edit, safe_respond
from utils.supabase_utils import supabase  # fonction pour requêtes supabase

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON des skills
# ────────────────────────────────────────────────────────────────────────────────
SKILL_JSON_PATH = os.path.join("data", "skills.json")
def load_skills():
    with open(SKILL_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Skill(commands.Cog):
    """
    Commande /skill et !skill — Utilise la compétence active de la classe du joueur
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.skills = load_skills()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _use_skill(self, user_id: int):
        """
        Vérifie la classe du joueur, le cooldown et applique la compétence active.
        Retourne un message embed à envoyer.
        """
        try:
            # Récupération des infos du joueur depuis Supabase
            resp = supabase.table("reiatsu").select("*").eq("user_id", user_id).single().execute()
            player = resp.data
            if not player:
                return discord.Embed(title="❌ Erreur", description="Aucune donnée trouvée pour ce joueur.", color=discord.Color.red())

            classe = player.get("classe")
            last_cd = player.get("comp_cd")
            now = datetime.utcnow()
            cooldown = timedelta(hours=8)

            if last_cd:
                last_used = datetime.fromisoformat(last_cd)
                if now - last_used < cooldown:
                    remaining = cooldown - (now - last_used)
                    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                    minutes = remainder // 60
                    return discord.Embed(
                        title="⏳ Skill en cooldown",
                        description=f"Tu dois attendre {hours}h {minutes}min avant de réutiliser ta compétence.",
                        color=discord.Color.orange()
                    )

            # Vérifie si la classe a une skill active
            classe_data = self.skills.get(classe)
            if not classe_data or "Active" not in classe_data:
                return discord.Embed(
                    title="⚠️ Pas de compétence active",
                    description="Ta classe n'a pas de compétence active.",
                    color=discord.Color.yellow()
                )

            skill_text = classe_data["Active"]
            # Met à jour le timestamp dans Supabase
            supabase.table("reiatsu").update({"comp_cd": now.isoformat()}).eq("user_id", user_id).execute()

            embed = discord.Embed(
                title=f"✅ Compétence utilisée : {classe}",
                description=skill_text,
                color=discord.Color.green()
            )
            return embed

        except Exception as e:
            print(f"[ERREUR _use_skill] {e}")
            return discord.Embed(title="❌ Erreur", description="Impossible d'utiliser la compétence.", color=discord.Color.red())

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="skill", description="Utilise la compétence active de ta classe (CD 8h).")
    async def slash_skill(self, interaction: discord.Interaction):
        """Commande slash principale"""
        try:
            await interaction.response.defer()
            embed = await self._use_skill(interaction.user.id)
            await safe_send(interaction.channel, embed=embed)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /skill] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue lors de l'utilisation de la compétence.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="skill")
    async def prefix_skill(self, ctx: commands.Context):
        """Commande préfixe principale"""
        try:
            embed = await self._use_skill(ctx.author.id)
            await safe_send(ctx.channel, embed=embed)
        except Exception as e:
            print(f"[ERREUR !skill] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors de l'utilisation de la compétence.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Skill(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
