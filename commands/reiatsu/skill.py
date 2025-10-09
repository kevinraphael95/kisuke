# ────────────────────────────────────────────────────────────────────────────────
# 📌 skill.py — Commande interactive /skill et !skill
# Objectif : Afficher et activer la compétence active du joueur
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
import asyncio
from dateutil import parser
from datetime import datetime, timedelta, timezone
import os
import json
from utils.discord_utils import safe_send, safe_respond
from utils.supabase_client import supabase
from utils.reiatsu_utils import ensure_profile, has_class

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
        self.skill_locks = {}

    # ────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne : activation du skill
    # ────────────────────────────────────────────────────────────────────────
    async def _activate_skill(self, user: discord.User, channel: discord.abc.Messageable):
        if user.id not in self.skill_locks:
            self.skill_locks[user.id] = asyncio.Lock()
        async with self.skill_locks[user.id]:
            # ✅ Création automatique du profil
            player = ensure_profile(user.id, user.name)
            # ❌ Si pas de classe
            if not has_class(player):
                await safe_send(channel, "❌ Tu n’as pas encore choisi de classe Reiatsu. Utilise `!!classe` pour choisir une classe.")
                return

            classe = player["classe"]
            classe_data = self.config["CLASSES"].get(classe, {})
            base_cd = classe_data.get("Cooldown", 12)

            # 🔹 Récupération du timestamp en base
            res = supabase.table("reiatsu").select("last_skilled_at, active_skill, fake_spawn_id").eq("user_id", user.id).execute()
            data = res.data[0] if res.data else {}
            last_skill = data.get("last_skilled_at")
            active_skill = data.get("active_skill", False)
            fake_spawn_id = data.get("fake_spawn_id")
            cooldown_text = "✅ Disponible"

            # 🔹 Calcul du cooldown
            if last_skill:
                try:
                    last_dt = parser.parse(last_skill)
                    if not last_dt.tzinfo:
                        last_dt = last_dt.replace(tzinfo=timezone.utc)
                    next_cd = last_dt + timedelta(hours=8 if classe == "Illusionniste" else base_cd)
                    now_dt = datetime.now(timezone.utc)
                    if now_dt < next_cd:
                        restant = next_cd - now_dt
                        h, m = divmod(int(restant.total_seconds() // 60), 60)
                        cooldown_text = f"⏳ {restant.days}j {h}h{m}m" if restant.days else f"⏳ {h}h{m}m"
                except:
                    pass

            if active_skill:
                cooldown_text = "🌀 En cours"

            # ⛔ Si en cooldown → affichage
            if cooldown_text != "✅ Disponible":
                embed = discord.Embed(
                    title=f"🎴 Skill de {player.get('username', user.name)}",
                    description=f"**Classe :** {classe}\n**Statut :** {cooldown_text}",
                    color=discord.Color.orange()
                )
                await safe_send(channel, embed=embed)
                return

            # 🔹 Activation du skill
            update_data = {"last_skilled_at": datetime.utcnow().isoformat()}
            msg = ""

            if classe == "Illusionniste":
                if fake_spawn_id:
                    await safe_send(channel, "⚠️ Tu as déjà un faux Reiatsu actif !")
                    return

                update_data["active_skill"] = True
                supabase.table("reiatsu").update(update_data).eq("user_id", user.id).execute()

                # Vérification du salon de spawn configuré
                conf_data = supabase.table("reiatsu_config").select("*").eq("guild_id", channel.guild.id).execute()
                if not conf_data.data or not conf_data.data[0].get("channel_id"):
                    await safe_send(channel, "❌ Aucun canal de spawn configuré pour ce serveur.")
                    return
                spawn_channel = self.bot.get_channel(int(conf_data.data[0]["channel_id"]))

                # Spawn du faux Reiatsu identique au vrai
                cog = self.bot.get_cog("ReiatsuSpawner")
                if cog:
                    await cog._spawn_message(spawn_channel, guild_id=None, is_fake=True, owner_id=user.id)

                # Message éphémère pour le joueur
                embed = discord.Embed(
                    title="🎭 Skill Illusionniste activé !",
                    description="Un faux Reiatsu est apparu dans le serveur…\nTu ne peux pas l’absorber toi-même.",
                    color=discord.Color.green()
                )
                await safe_send(channel, embed=embed, ephemeral=True)

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

            # ✅ Mise à jour Supabase pour les autres classes
            if classe != "Illusionniste":
                supabase.table("reiatsu").update(update_data).eq("user_id", user.id).execute()
                embed = discord.Embed(
                    title=f"🎴 Skill de {player.get('username', user.name)}",
                    description=f"**Classe :** {classe}\n**Statut :** 🌀 En cours\n\n{msg}",
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


