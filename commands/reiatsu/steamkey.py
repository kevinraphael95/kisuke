# ────────────────────────────────────────────────────────────────────────────────
# 📌 steamkey.py — Commande interactive /steamkey et !steamkey
# Objectif : Miser des points Reiatsu pour tenter de gagner une clé Steam
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Constantes
# ────────────────────────────────────────────────────────────────────────────────
REIATSU_COST = 1
WIN_CHANCE = 0.5  # 50% de chance de gagner

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — View avec bouton miser
# ────────────────────────────────────────────────────────────────────────────────
class SteamKeyView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.value = None
        self.last_interaction = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await safe_respond(interaction, "❌ Ce bouton n'est pas pour toi.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label=f"Miser {REIATSU_COST} Reiatsu", style=discord.ButtonStyle.green)
    async def bet_button(self, interaction: discord.Interaction, button: Button):
        button.disabled = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.value = True
        self.last_interaction = interaction
        self.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Confirmation avec possibilité de choisir un autre jeu
# ────────────────────────────────────────────────────────────────────────────────
class ConfirmKeyView(View):
    def __init__(self, author_id: int, keys_dispo: list, current_key: dict):
        super().__init__(timeout=30)
        self.author_id = author_id
        self.keys_dispo = keys_dispo
        self.current_key = current_key
        self.choice = None  # "accept", "reject"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @discord.ui.button(label="✅ Oui, je veux la clé", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.choice = "accept"
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="🎲 Autre jeu", style=discord.ButtonStyle.blurple)
    async def other_game(self, interaction: discord.Interaction, button: Button):
        if len(self.keys_dispo) <= 1:
            await safe_respond(interaction, "⚠️ Aucun autre jeu disponible.", ephemeral=True)
            return

        current_index = next((i for i, k in enumerate(self.keys_dispo) if k["id"] == self.current_key["id"]), 0)
        next_index = (current_index + 1) % len(self.keys_dispo)
        self.current_key = self.keys_dispo[next_index]

        embed = discord.Embed(
            title="🎲 Nouveau jeu proposé !",
            description="Voici le jeu que tu peux remporter :",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Jeu", value=self.current_key["game_name"], inline=True)
        embed.add_field(name="Lien Steam", value=f"[Voir sur Steam]({self.current_key['steam_url']})", inline=True)
        embed.set_footer(text="Tu peux confirmer pour recevoir cette clé ou demander un autre jeu.")

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Non, laisse la clé", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        self.choice = "reject"
        await interaction.response.defer()
        self.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class SteamKey(commands.Cog):
    """Commande /steamkey et !steamkey — Miser des Reiatsu pour tenter de gagner une clé Steam"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_reiatsu(self, user_id: str) -> int:
        resp = supabase.table("reiatsu").select("points").eq("user_id", user_id).single().execute()
        return resp.data["points"] if resp.data else 0

    async def _update_reiatsu(self, user_id: str, new_points: int):
        supabase.table("reiatsu").update({"points": new_points}).eq("user_id", user_id).execute()

    async def _get_all_steam_keys(self):
        resp = supabase.table("steam_keys").select("*").eq("won", False).execute()
        return resp.data if resp.data else []

    async def _mark_steam_key_won(self, key_id: int, winner: str):
        supabase.table("steam_keys").update({"won": True, "winner": winner}).eq("id", key_id).execute()

    async def _try_win_key(self, interaction_or_ctx):
        keys_dispo = await self._get_all_steam_keys()
        if not keys_dispo:
            await self._send(interaction_or_ctx, discord.Embed(
                title="⛔ Impossible de miser",
                description="Aucune clé disponible pour le moment.",
                color=discord.Color.orange()
            ))
            return

        user_id = str(interaction_or_ctx.user.id)
        reiatsu_points = await self._get_reiatsu(user_id)
        if reiatsu_points < REIATSU_COST:
            msg = f"❌ Tu n'as pas assez de Reiatsu (il te faut {REIATSU_COST})."
            if isinstance(interaction_or_ctx, discord.Interaction):
                await interaction_or_ctx.followup.send(msg, ephemeral=True)
            else:
                await safe_send(interaction_or_ctx.channel, msg)
            return

        await self._update_reiatsu(user_id, reiatsu_points - REIATSU_COST)

        if random.random() <= WIN_CHANCE:
            key = keys_dispo[0]
            embed = discord.Embed(
                title="🎉 Félicitations !",
                description="Tu as gagné une clé Steam !",
                color=discord.Color.green()
            )
            embed.add_field(name="Jeu", value=key["game_name"], inline=True)
            embed.add_field(name="Lien Steam", value=f"[Voir sur Steam]({key['steam_url']})", inline=True)
            embed.set_footer(text="Confirme si tu veux recevoir la clé ou demande un autre jeu.")

            view = ConfirmKeyView(interaction_or_ctx.user.id, keys_dispo, key)
            msg = await self._send(interaction_or_ctx, embed, view)
            await view.wait()

            if view.choice == "accept":
                await self._mark_steam_key_won(view.current_key["id"], interaction_or_ctx.user.name)
                try:
                    await interaction_or_ctx.user.send(f"🎁 **Clé Steam pour {view.current_key['game_name']}**\n`{view.current_key['steam_key']}`")
                    await safe_edit(msg, embed=discord.Embed(title="✅ Clé envoyée en DM !", color=discord.Color.green()), view=None)
                except discord.Forbidden:
                    await safe_edit(msg, embed=discord.Embed(title="⚠️ Impossible d'envoyer un DM.", color=discord.Color.orange()), view=None)
            elif view.choice == "reject":
                await safe_edit(msg, embed=discord.Embed(title="🔄 Clé laissée dispo pour les autres joueurs.", color=discord.Color.blurple()), view=None)
        else:
            await self._send(interaction_or_ctx, discord.Embed(
                title="Dommage !",
                description="❌ Tu n'as pas gagné cette fois, retente ta chance !",
                color=discord.Color.red()
            ))

    async def _send(self, interaction_or_ctx, embed, view=None):
        if isinstance(interaction_or_ctx, discord.Interaction):
            return await interaction_or_ctx.followup.send(embed=embed, view=view)
        return await safe_send(interaction_or_ctx.channel, embed=embed, view=view)

    @app_commands.command(name="steamkey", description="Miser des Reiatsu pour tenter de gagner une clé Steam")
    async def slash_steamkey(self, interaction: discord.Interaction):
        try:
            view = SteamKeyView(interaction.user.id)
            await safe_send(interaction.channel, "Clique sur miser pour tenter ta chance !", view=view)
            await view.wait()
            if view.value:
                await self._try_win_key(view.last_interaction)
        except Exception as e:
            print(f"[ERREUR /steamkey] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="steamkey", aliases=["sk"])
    async def prefix_steamkey(self, ctx: commands.Context):
        try:
            view = SteamKeyView(ctx.author.id)
            await safe_send(ctx.channel, "Clique sur miser pour tenter ta chance !", view=view)
            await view.wait()
            if view.value:
                class DummyInteraction:
                    def __init__(self, user, channel): self.user, self.channel = user, channel
                await self._try_win_key(DummyInteraction(ctx.author, ctx.channel))
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
