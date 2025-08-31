# ────────────────────────────────────────────────────────────────────────────────
# 📌 steamkey.py — Commande interactive /steamkey et !steamkey
# Objectif : Miser des points Reiatsu pour tenter de gagner une clé Steam
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import os
import random
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_edit, safe_respond  # ✅ Utilisation safe_* functions

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement & constantes
# ────────────────────────────────────────────────────────────────────────────────
REIATSU_COST = 1
WIN_CHANCE = 0.5  # 0.01 pour 1% de chance de gagner
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — View avec bouton miser
# ────────────────────────────────────────────────────────────────────────────────
class SteamKeyView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.value = None  # Pour savoir si pari validé
        self.last_interaction = None  # ✅ stocker la dernière interaction

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await safe_respond(interaction, "❌ Ce bouton n'est pas pour toi.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label=f"Miser {REIATSU_COST} Reiatsu", style=discord.ButtonStyle.green)
    async def bet_button(self, interaction: discord.Interaction, button: Button):
        # Désactive le bouton
        button.disabled = True
        await interaction.response.edit_message(view=self)
        self.value = True
        self.last_interaction = interaction  # ✅ on stocke
        self.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class SteamKey(commands.Cog):
    """Commande /steamkey et !steamkey — Miser des Reiatsu pour tenter de gagner une clé Steam"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonctions internes accès Supabase
    # ────────────────────────────────────────────────────────────────────────────────
    async def _get_reiatsu(self, user_id: str) -> int:
        response = supabase.table("reiatsu").select("points").eq("user_id", user_id).single().execute()
        if response.data:
            return response.data["points"]
        return 0

    async def _update_reiatsu(self, user_id: str, new_points: int):
        supabase.table("reiatsu").update({"points": new_points}).eq("user_id", user_id).execute()

    async def _get_one_steam_key(self):
        response = supabase.table("steam_keys").select("*").limit(1).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None

    async def _delete_steam_key(self, key_id: int):
        supabase.table("steam_keys").delete().eq("id", key_id).execute()

    # ────────────────────────────────────────────────────────────────────────────────
    # 🔹 Logique du jeu après pari
    # ────────────────────────────────────────────────────────────────────────────────
    async def _try_win_key(self, interaction_or_ctx):
        """Logique pour savoir si l'utilisateur gagne une clé."""
        user_id = str(interaction_or_ctx.user.id)
        reiatsu_points = await self._get_reiatsu(user_id)

        # Vérification des points
        if reiatsu_points < REIATSU_COST:
            if isinstance(interaction_or_ctx, discord.Interaction):
                await interaction_or_ctx.followup.send(
                    f"❌ Tu n'as pas assez de Reiatsu (il te faut {REIATSU_COST}).",
                    ephemeral=True
                )
            else:
                await safe_send(interaction_or_ctx.channel, f"❌ Tu n'as pas assez de Reiatsu (il te faut {REIATSU_COST}).")
            return

        # Déduction des points
        await self._update_reiatsu(user_id, reiatsu_points - REIATSU_COST)

        # Détermination du résultat
        if random.random() <= WIN_CHANCE:
            key = await self._get_one_steam_key()
            if not key:
                embed = discord.Embed(
                    title="🎮 Jeu Steam Key - Résultat",
                    description="🎉 Tu as gagné ! Mais il n'y a plus de clés disponibles 😢",
                    color=discord.Color.gold()
                )
            else:
                await self._delete_steam_key(key["id"])
                embed = discord.Embed(
                    title="🎉 Félicitations, tu as gagné une clé Steam !",
                    color=discord.Color.green()
                )
                embed.add_field(name="Jeu", value=key["game_name"], inline=True)
                embed.add_field(name="Lien Steam", value=f"[Clique ici]({key['steam_url']})", inline=True)
                embed.add_field(name="Clé Steam", value=f"`{key['steam_key']}`", inline=False)
        else:
            embed = discord.Embed(
                title="Jeu Steam Key - Résultat",
                description="❌ Désolé, tu n'as pas gagné cette fois. Retente ta chance !",
                color=discord.Color.red()
            )

        # Envoi du résultat
        if isinstance(interaction_or_ctx, discord.Interaction):
            await interaction_or_ctx.followup.send(embed=embed)
        else:
            await safe_send(interaction_or_ctx.channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────────
    # 🔹 Envoi du menu interactif
    # ────────────────────────────────────────────────────────────────────────────────
    async def _send_menu(self, channel: discord.abc.Messageable, user_id: int):
        keys_resp = supabase.table("steam_keys").select("game_name").execute()
        nb_keys = len(keys_resp.data) if keys_resp.data else 0
        games = set(k["game_name"] for k in keys_resp.data) if keys_resp.data else set()

        embed = discord.Embed(
            title="🎮 Jeu Steam Key",
            description=f"Miser {REIATSU_COST} Reiatsu pour avoir une faible chance de gagner une clé Steam.",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Probabilité de gagner une clé", value="50%", inline=False)
        embed.add_field(name="Nombre de clés disponibles", value=str(nb_keys), inline=False)
        embed.add_field(name="Jeux possibles à gagner", value=", ".join(games) if games else "Aucun", inline=True)
        embed.set_footer(text="Vous avez 2 minutes pour miser.")

        view = SteamKeyView(user_id)
        await safe_send(channel, embed=embed, view=view)
        return view

    # ────────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="steamkey", description="Miser des Reiatsu pour tenter de gagner une clé Steam")
    async def slash_steamkey(self, interaction: discord.Interaction):
        try:
            # ⚠️ Pas de defer ici, pour que le bouton puisse fonctionner
            view = await self._send_menu(interaction.channel, interaction.user.id)
            await view.wait()

            if view.value:
                await self._try_win_key(view.last_interaction)
            else:
                for child in view.children:
                    child.disabled = True
                msg = await interaction.original_response()
                await safe_edit(msg, view=view)
                await safe_respond(interaction, "⏰ Temps écoulé, la mise a été annulée.", ephemeral=True)

        except Exception as e:
            print(f"[ERREUR /steamkey] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────────
    @commands.command(name="steamkey", aliases=["sk"], description="Miser des Reiatsu pour tenter de gagner une clé Steam")
    async def prefix_steamkey(self, ctx: commands.Context):
        try:
            view = await self._send_menu(ctx.channel, ctx.author.id)
            await view.wait()

            if view.value:
                # On réutilise le même pipeline que slash
                class DummyInteraction:
                    def __init__(self, user, channel):
                        self.user = user
                        self.channel = channel

                dummy_inter = DummyInteraction(ctx.author, ctx.channel)
                await self._try_win_key(dummy_inter)
            else:
                await safe_send(ctx.channel, "⏰ Temps écoulé, la mise a été annulée.")
        except Exception as e:
            print(f"[ERREUR !steamkey] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SteamKey(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
