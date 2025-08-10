# ────────────────────────────────────────────────────────────────────────────────
# 📌 steamkey.py — Commande interactive !steamkey
# Objectif : Tenter de gagner une clé Steam contre des Reiatsu
# Catégorie : Reiatsu
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
import random
from supabase import create_client, Client
from discord_utils import safe_send, safe_respond
import os

# ────────────────────────────────────────────────────────────────────────────────
# 📂 CONSTANTES
# ────────────────────────────────────────────────────────────────────────────────
REIATSU_COST = 50
WIN_CHANCE = 0.01  # 1%
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog SteamKey
# ────────────────────────────────────────────────────────────────────────────────
class SteamKey(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ──────────────────────────────
    # 🔑 Fonction principale
    # ──────────────────────────────
    async def _steamkey_logic(self, ctx_or_interaction, user_id: int, is_slash: bool):
        """
        Fonction principale pour tenter de gagner une clé Steam.
        """
        try:
            # Récupération du solde Reiatsu
            response = supabase.table("reiatsu_users").select("reiatsu").eq("user_id", str(user_id)).single().execute()
            if not response.data:
                msg = "❌ Vous n'avez pas encore de Reiatsu enregistré."
                if is_slash:
                    return await safe_respond(ctx_or_interaction, msg)
                else:
                    return await safe_send(ctx_or_interaction, msg)

            reiatsu_amount = response.data["reiatsu"]
            if reiatsu_amount < REIATSU_COST:
                msg = f"❌ Il vous faut **{REIATSU_COST} Reiatsu** pour tenter votre chance."
                if is_slash:
                    return await safe_respond(ctx_or_interaction, msg)
                else:
                    return await safe_send(ctx_or_interaction, msg)

            # Déduction immédiate
            supabase.table("reiatsu_users").update({"reiatsu": reiatsu_amount - REIATSU_COST}).eq("user_id", str(user_id)).execute()

            # Tirage
            if random.random() <= WIN_CHANCE:
                # Récupération d'une clé
                key_data = supabase.table("steam_keys").select("*").limit(1).execute()
                if not key_data.data:
                    msg = "🎉 Vous avez gagné ! Mais... il n'y a plus de clés Steam disponibles 😅"
                    if is_slash:
                        return await safe_respond(ctx_or_interaction, msg)
                    else:
                        return await safe_send(ctx_or_interaction, msg)

                key = key_data.data[0]
                # Suppression de la clé
                supabase.table("steam_keys").delete().eq("id", key["id"]).execute()

                # Embed victoire
                embed = discord.Embed(
                    title="🎉 Félicitations !",
                    description=f"Vous avez gagné une clé Steam pour **{key['game_name']}** !",
                    color=discord.Color.green()
                )
                embed.add_field(name="🔑 Clé Steam", value=f"||{key['steam_key']}||", inline=False)
                embed.add_field(name="🔗 Page Steam", value=key["steam_url"], inline=False)
                if is_slash:
                    return await safe_respond(ctx_or_interaction, embed=embed)
                else:
                    return await safe_send(ctx_or_interaction, embed=embed)

            else:
                # Embed défaite
                embed = discord.Embed(
                    title="💨 Pas de chance...",
                    description=f"Vous avez perdu. **{REIATSU_COST} Reiatsu** ont été dépensés.",
                    color=discord.Color.red()
                )
                if is_slash:
                    return await safe_respond(ctx_or_interaction, embed=embed)
                else:
                    return await safe_send(ctx_or_interaction, embed=embed)

        except Exception as e:
            msg = f"❌ Une erreur est survenue : `{e}`"
            if is_slash:
                return await safe_respond(ctx_or_interaction, msg)
            else:
                return await safe_send(ctx_or_interaction, msg)

    # ──────────────────────────────
    # ⚙️ Commande préfixe
    # ──────────────────────────────
    @commands.command(name="steamkey")
    async def steamkey_prefix(self, ctx):
        """Tenter de gagner une clé Steam (coût : 50 Reiatsu)."""
        await self._steamkey_logic(ctx, ctx.author.id, is_slash=False)

    # ──────────────────────────────
    # ⚙️ Commande slash
    # ──────────────────────────────
    @app_commands.command(name="steamkey", description="Tenter de gagner une clé Steam (coût : 50 Reiatsu).")
    async def steamkey_slash(self, interaction: discord.Interaction):
        await self._steamkey_logic(interaction, interaction.user.id, is_slash=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SteamKey(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)

