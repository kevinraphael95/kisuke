# ────────────────────────────────────────────────────────────────────────────────
# 📌 skill.py — Commande simple /skill et !skill
# Objectif : Utiliser la compétence active de la classe du joueur avec cooldown
# Catégorie : Reiatsu
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import random
from datetime import datetime, timezone, timedelta
import discord
from discord import app_commands
from discord.ext import commands
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_followup

# Cooldowns par classe (en secondes)
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
    """
    Commande /skill et !skill — Active la compétence spécifique de la classe du joueur avec cooldown
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("[COG LOAD] Skill cog chargé ✅")

    # 🔹 Fonction interne commune
    async def _execute_skill(self, user_id: str, ctx_or_interaction=None):
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

        # ⏳ Cooldown
        if last_skill:
            elapsed = (now - datetime.fromisoformat(last_skill)).total_seconds()
            if elapsed < skill_cd:
                remaining = timedelta(seconds=int(skill_cd - elapsed))
                return f"⏳ Compétence encore en recharge ! Temps restant : **{remaining}**"

        updated_fields = {}
        result_message = ""

        # ────── Gestion des compétences par classe ──────
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

            # 🔹 Trouver un canal de spawn
            conf_data = supabase.table("reiatsu_config").select("*").limit(1).execute()
            if not conf_data.data:
                return "❌ Impossible de trouver le canal pour le faux Reiatsu."
            channel_id = int(conf_data.data[0].get("channel_id"))
            guild_id = int(conf_data.data[0].get("guild_id"))
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return "❌ Guild introuvable."
            channel = guild.get_channel(channel_id)
            if not channel:
                return "❌ Canal introuvable."

            # 🔹 Créer le faux Reiatsu identique au spawn automatique
            embed = discord.Embed(
                title="💠 Un Reiatsu sauvage apparaît !",
                description="Cliquez sur la réaction 💠 pour l'absorber.",
                color=discord.Color.purple()
            )
            fake_message = await safe_send(channel, embed=embed)
            spawn_id = str(fake_message.id) if fake_message else None
            if fake_message:
                try:
                    await fake_message.add_reaction("💠")
                except discord.HTTPException:
                    pass

            updated_fields["active_skill"] = {
                "type": "faux",
                "owner_id": user_id,
                "points": 0,
                "spawn_id": spawn_id,
                "created_at": now.isoformat()
            }
            updated_fields["faux_block_user"] = user_id
            result_message = "🎭 Tu as créé un faux Reiatsu ! Si quelqu’un le prend → tu gagnes **+10 points**."
            new_cd = CLASS_CD["Illusionniste"]

            # 🔹 Supprimer le message de commande pour effacer les traces
            if ctx_or_interaction:
                try:
                    if isinstance(ctx_or_interaction, commands.Context):
                        await ctx_or_interaction.message.delete()
                    elif isinstance(ctx_or_interaction, discord.Interaction):
                        if ctx_or_interaction.response.is_done():
                            await ctx_or_interaction.delete_original_response()
                        else:
                            await ctx_or_interaction.response.defer()
                            await ctx_or_interaction.delete_original_response()
                except Exception:
                    pass

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

        updated_fields["last_skill"] = now.isoformat()
        updated_fields["skill_cd"] = new_cd

        try:
            supabase.table("reiatsu").update(updated_fields).eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[ERREUR SUPABASE UPDATE] {e}")
            return "❌ Impossible de mettre à jour les données."

        return result_message

    # 🔹 Listener pour gérer l'absorption du faux Reiatsu
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "💠":
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception:
            return

        # Vérifier si c'est un faux Reiatsu
        response = supabase.table("reiatsu").select("*").execute()
        data_list = getattr(response, "data", [])
        faux_data = None
        for data in data_list:
            active_skill = data.get("active_skill")
            if active_skill and active_skill.get("spawn_id") == str(payload.message_id):
                faux_data = data
                break
        if not faux_data:
            return

        faux_owner_id = faux_data["active_skill"].get("owner_id")
        faux_block_user = faux_data.get("faux_block_user")
        if str(payload.user_id) == str(faux_block_user):
            return

        try:
            # Récupérer les points actuels pour éviter l'écrasement
            current_points = supabase.table("reiatsu").select("points").eq("user_id", str(faux_owner_id)).single().execute().data["points"]
            supabase.table("reiatsu").update({
                "points": current_points + 10,
                "active_skill": None,
                "faux_block_user": None
            }).eq("user_id", str(faux_owner_id)).execute()
        except Exception as e:
            print(f"[ERREUR SUPABASE UPDATE FAUX REIATSU] {e}")
            return

        try:
            await message.delete()
        except Exception:
            pass

    # 🔹 Commande SLASH
    @app_commands.command(
        name="skill",
        description="Active la compétence spécifique de ta classe avec cooldown."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_skill(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            message = await self._execute_skill(str(interaction.user.id), interaction)
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
            message = await self._execute_skill(str(ctx.author.id), ctx)
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
