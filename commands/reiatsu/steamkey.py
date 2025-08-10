# =========================
# COMMANDE : steamkey
# Catégorie : Reiatsu
# =========================

import discord
from discord.ext import commands
from discord import app_commands
import random
from supabase import create_client, Client
from discord_utils import safe_send, safe_respond
import os

# =========================
# CONSTANTES
# =========================
REIATSU_COST = 50
WIN_CHANCE = 0.01  # 1%
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class Reiatsu(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # =========================
    # FONCTION COMMUNE
    # =========================
    async def _steamkey_logic(self, ctx_or_interaction, user_id: int, is_slash: bool):
        """
        Fonction principale pour tenter de gagner une clé Steam.
        """
        # Récupération du solde Reiatsu
        try:
            response = supabase.table("reiatsu_users").select("reiatsu").eq("user_id", str(user_id)).single().execute()
            if not response.data:
                msg = "❌ Vous n'avez pas encore de Reiatsu enregistré."
                return await safe_respond(ctx_or_interaction, msg) if is_slash else await safe_send(ctx_or_interaction, msg)

            reiatsu_amount = response.data["reiatsu"]

            if reiatsu_amount < REIATSU_COST:
                msg = f"❌ Il vous faut **{REIATSU_COST} Reiatsu** pour tenter votre chance."
                return await safe_respond(ctx_or_interaction, msg) if is_slash else await safe_send(ctx_or_interaction, msg)

            # Déduction immédiate
            supabase.table("reiatsu_users").update({"reiatsu": reiatsu_amount - REIATSU_COST}).eq("user_id", str(user_id)).execute()

            # Tirage
            if random.random() <= WIN_CHANCE:
                # Récupération d'une clé
                key_data = supabase.table("steam_keys").select("*").limit(1).execute()
                if not key_data.data:
                    msg = "🎉 Vous avez gagné ! Mais... il n'y a plus de clés Steam disponibles 😅"
                    return await safe_respond(ctx_or_interaction, msg) if is_slash else await safe_send(ctx_or_interaction, msg)

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
                return await safe_respond(ctx_or_interaction, embed=embed) if is_slash else await safe_send(ctx_or_interaction, embed=embed)

            else:
                # Embed défaite
                embed = discord.Embed(
                    title="💨 Pas de chance...",
                    description=f"Vous avez perdu. **{REIATSU_COST} Reiatsu** ont été dépensés.",
                    color=discord.Color.red()
                )
                return await safe_respond(ctx_or_interaction, embed=embed) if is_slash else await safe_send(ctx_or_interaction, embed=embed)

        except Exception as e:
            msg = f"❌ Une erreur est survenue : `{e}`"
            return await safe_respond(ctx_or_interaction, msg) if is_slash else await safe_send(ctx_or_interaction, msg)

    # =========================
    # COMMANDE PRÉFIXE
    # =========================
    @commands.command(name="steamkey")
    async def steamkey_prefix(self, ctx):
        """Tenter de gagner une clé Steam (coût : 50 Reiatsu)."""
        await self._steamkey_logic(ctx, ctx.author.id, is_slash=False)

    # =========================
    # COMMANDE SLASH
    # =========================
    @app_commands.command(name="steamkey", description="Tenter de gagner une clé Steam (coût : 50 Reiatsu).")
    async def steamkey_slash(self, interaction: discord.Interaction):
        await self._steamkey_logic(interaction, interaction.user.id, is_slash=True)


async def setup(bot: commands.Bot):
    cog = ReiatsuVol(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
