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
import os

from supabase import create_client, Client
from discord_utils import safe_send, safe_respond  # Fonctions anti-429 pour éviter les ratelimits

# ────────────────────────────────────────────────────────────────────────────────
# 📂 CONSTANTES
# ────────────────────────────────────────────────────────────────────────────────
REIATSU_COST = 50
WIN_CHANCE = 0.01  # 1%
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal — SteamKey
# ────────────────────────────────────────────────────────────────────────────────
class SteamKey(commands.Cog):
    """
    Commande !steamkey — Tente ta chance pour gagner une clé Steam en dépensant des Reiatsu.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[SteamKey] Cog chargé correctement.")

    # ────────────────────────────────────────────────────────────────────────────────
    # 🔑 Fonction interne commune — utilisée par préfixe & slash
    # ────────────────────────────────────────────────────────────────────────────────
    async def _steamkey_logic(self, ctx_or_interaction, user_id: int, is_slash: bool):
        """
        Logique principale du jeu : vérifie les Reiatsu (points), tente la chance, renvoie un message.
        """
        # Récupération des points Reiatsu du joueur
        response = supabase.table("reiatsu") \
            .select("points, username") \
            .eq("user_id", str(user_id)) \
            .single() \
            .execute()

        if not response.data:
            msg = "❌ Vous n'avez pas encore de Reiatsu enregistré."
            if is_slash:
                if not ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.response.send_message(msg, ephemeral=True)
                else:
                    await ctx_or_interaction.followup.send(msg, ephemeral=True)
            else:
                await safe_send(ctx_or_interaction, msg)
            return

        reiatsu_amount = response.data["points"]
        username = response.data.get("username", "Joueur")

        if reiatsu_amount < REIATSU_COST:
            msg = f"❌ Il vous faut **{REIATSU_COST} Reiatsu** pour tenter votre chance."
            if is_slash:
                if not ctx_or_interaction.response.is_done():
                    await ctx_or_interaction.response.send_message(msg, ephemeral=True)
                else:
                    await ctx_or_interaction.followup.send(msg, ephemeral=True)
            else:
                await safe_send(ctx_or_interaction, msg)
            return

        # Déduction immédiate des Reiatsu (points)
        supabase.table("reiatsu") \
            .update({"points": reiatsu_amount - REIATSU_COST}) \
            .eq("user_id", str(user_id)) \
            .execute()

        # Tentative de gain
        if random.random() <= WIN_CHANCE:
            key_data = supabase.table("steam_keys") \
                .select("id, game_name, steam_url, steam_key") \
                .limit(1) \
                .execute()

            if not key_data.data:
                msg = "🎉 Vous avez gagné ! Mais... il n'y a malheureusement plus de clés disponibles."
            else:
                key = key_data.data[0]
                key_id = key["id"]
                game_name = key["game_name"]
                steam_url = key["steam_url"]
                steam_key = key["steam_key"]

                # Suppression de la clé gagnée de la base
                supabase.table("steam_keys").delete().eq("id", key_id).execute()

                msg = (
                    f"🎉 Félicitations {username} ! Vous avez gagné une clé Steam pour **{game_name}** !\n"
                    f"🔑 Clé : `{steam_key}`\n"
                    f"🌐 URL Steam : {steam_url}"
                )
        else:
            msg = "❌ Désolé, vous n'avez pas gagné cette fois. Retentez votre chance !"

        # Envoi adapté selon type d'appel
        if is_slash:
            if not ctx_or_interaction.response.is_done():
                await ctx_or_interaction.response.send_message(msg)
            else:
                await ctx_or_interaction.followup.send(msg)
        else:
            await safe_send(ctx_or_interaction, msg)

    # ────────────────────────────────────────────────────────────────────────────────
    # ⌨️ Commande préfixe
    # ────────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="steamkey",
        aliases=["sk"],
        help="🎮 Tente de gagner une clé Steam en dépensant des Reiatsu.",
        description="Dépense 50 Reiatsu pour tenter de remporter une clé Steam."
    )
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def steamkey(self, ctx: commands.Context):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"[ERREUR suppression message !steamkey] {e}")

        await self._steamkey_logic(ctx, ctx.author.id, is_slash=False)

    # ────────────────────────────────────────────────────────────────────────────────
    # 💬 Commande slash
    # ────────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="steamkey",
        description="🎮 Tente de gagner une clé Steam en dépensant des Reiatsu."
    )
    async def steamkey_slash(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)
            await self._steamkey_logic(interaction, interaction.user.id, is_slash=True)
        except Exception as e:
            print(f"[ERREUR /steamkey] {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Une erreur est survenue.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Une erreur est survenue.", ephemeral=True)
            except:
                pass

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SteamKey(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)


