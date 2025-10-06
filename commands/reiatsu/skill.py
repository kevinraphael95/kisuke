# ────────────────────────────────────────────────────────────────────────────────
# 📌 skill.py — Commande interactive /skill et !skill
# Objectif : Afficher et activer la compétence active de la classe du joueur
# (Illusionniste, Voleur, Absorbeur, Parieur)
# Catégorie : Reiatsu
# Accès : Tous
# Cooldown : 12h (8h pour Illusionniste)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import datetime
import os
import json
import asyncio
from utils.discord_utils import safe_send, safe_respond
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement de la configuration Reiatsu
# ────────────────────────────────────────────────────────────────────────────────
REIATSU_CONFIG_PATH = os.path.join("data", "reiatsu_config.json")
def load_reiatsu_config():
    """Charge la configuration Reiatsu depuis le fichier JSON."""
    try:
        with open(REIATSU_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {REIATSU_CONFIG_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal : Skill
# ────────────────────────────────────────────────────────────────────────────────
class Skill(commands.Cog):
    """Commande /skill et !skill — Active la compétence active du joueur."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_reiatsu_config()
        self.skill_locks = {}  # Lock pour chaque utilisateur

    # ────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne : activation du skill
    # ────────────────────────────────────────────────────────────────────────
    async def _activate_skill(self, user: discord.User, channel: discord.abc.Messageable):
        """Vérifie la classe, calcule le cooldown et active la compétence correspondante."""
        if user.id not in self.skill_locks:
            self.skill_locks[user.id] = asyncio.Lock()

        async with self.skill_locks[user.id]:
            res = supabase.table("reiatsu").select("*").eq("user_id", user.id).execute()
            if not res.data:
                await safe_send(channel, "❌ Tu n'as pas encore de profil Reiatsu. Utilise `!!reiatsu` pour en créer un.")
                return
            player = res.data[0]
            classe = player.get("classe", "Travailleur")
            now = datetime.datetime.utcnow()

            # Cooldown selon classe
            cooldown_h = 8 if classe == "Illusionniste" else 12
            last_skill = player.get("last_skilled_at")
            remaining = 0
            if last_skill:
                try:
                    elapsed = (now - datetime.datetime.fromisoformat(last_skill)).total_seconds() / 3600
                    remaining = max(0, cooldown_h - elapsed)
                except Exception:
                    remaining = 0

            if remaining > 0:
                await safe_send(channel, f"⏳ Tu dois attendre {remaining:.1f}h avant de réutiliser ton skill.")
                return  # Bloque l’activation si le cooldown n’est pas fini

            cooldown_text = "✅ Prêt à utiliser !"
            update_data = {"last_skilled_at": now.isoformat()}
            msg = ""

            # Gestion des classes
            if classe == "Illusionniste":
                update_data["active_skill"] = True
                msg = "🎭 **Illusion activée !** Un faux Reiatsu apparaîtra bientôt."
            elif classe == "Voleur":
                update_data["active_skill"] = True
                msg = "🥷 **Vol garanti activé !** Ton prochain vol réussira à coup sûr."
            elif classe == "Absorbeur":
                update_data["active_skill"] = True
                msg = "🌀 **Super Absorption !** Le prochain Reiatsu sera forcément un Super Reiatsu."
            elif classe == "Parieur":
                points = player.get("points", 0)
                if points < 10:
                    await safe_send(channel, "❌ Tu n'as pas assez de Reiatsu pour parier (10 requis).")
                    return
                import random
                gain = 30
                if random.random() < 0.5:
                    update_data["points"] = points - 10
                    msg = "🎲 **Perdu !** Tu as perdu 10 Reiatsu."
                else:
                    update_data["points"] = points - 10 + gain
                    msg = f"🎲 **Gagné !** Tu as misé 10 Reiatsu et remporté **{gain}**."
            else:
                msg = "👶 Cette classe n’a pas de compétence active."

            # Mise à jour Supabase
            supabase.table("reiatsu").update(update_data).eq("user_id", user.id).execute()

            # Message embed
            embed = discord.Embed(
                title=f"🎭 Compétence de {classe} ({player.get('username', user.name)})",
                description=f"{msg}\n\n{cooldown_text}",
                color=discord.Color.green()
            )
            await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="skill", description="Active la compétence de ta classe Reiatsu.")
    @app_commands.checks.cooldown(rate=1, per=5.0, key=lambda i: i.user.id)
    async def slash_skill(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._activate_skill(interaction.user, interaction.channel)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────
    @commands.command(name="skill", help="Active la compétence de ta classe Reiatsu.")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_skill(self, ctx: commands.Context):
        await self._activate_skill(ctx.author, ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Skill(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)


