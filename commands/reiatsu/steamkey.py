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
WIN_CHANCE = 0.5  # 50%

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
# 🎛️ UI — Confirmation avec choix du jeu
# ────────────────────────────────────────────────────────────────────────────────

class ConfirmKeyView(View):
    def __init__(self, author_id: int, keys_dispo: list, message: discord.Message, current_index: int = 0):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.keys_dispo = keys_dispo
        self.index = current_index
        self.message = message
        self.choice = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @property
    def current_key(self):
        return self.keys_dispo[self.index]

    def build_embed(self):
        embed = discord.Embed(
            title="🎉 Félicitations !",
            description="Tu as gagné une clé Steam ! Choisis ton jeu :",
            color=discord.Color.green()
        )
        embed.add_field(name="🎮 Jeu", value=self.current_key["game_name"], inline=True)
        embed.add_field(name="🔗 Lien Steam", value=f"[Voir sur Steam]({self.current_key['steam_url']})", inline=True)
        embed.set_footer(text="✅ : Recevoir cette clé en DM | 🎲 : Voir un autre jeu | ❌ : Refuser")
        return embed

    async def refresh_embed(self, interaction: discord.Interaction):
        await safe_edit(self.message, embed=self.build_embed(), view=self)
        await interaction.response.defer()

    @discord.ui.button(label="✅ Oui, je veux cette clé", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.choice = "accept"
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="🎲 Autre jeu", style=discord.ButtonStyle.blurple)
    async def other_game(self, interaction: discord.Interaction, button: Button):
        self.index = (self.index + 1) % len(self.keys_dispo)
        await self.refresh_embed(interaction)

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

    async def _send_intro_embed(self, interaction_or_ctx, reiatsu_points, keys):
        jeux_list = ", ".join([k['game_name'] for k in keys[:5]]) + ("..." if len(keys) > 5 else "")
        embed = discord.Embed(
            title="🎲 Mise pour tenter de gagner une clé Steam",
            description="Utilise tes Reiatsu pour tenter ta chance !",
            color=discord.Color.blurple()
        )
        embed.add_field(name="💠 Reiatsu possédés", value=f"**{reiatsu_points}**", inline=True)
        embed.add_field(name="💰 Prix d'une mise", value=f"**{REIATSU_COST}**", inline=True)
        embed.add_field(name="🎯 Chance de gain", value=f"**{int(WIN_CHANCE*100)} %**", inline=True)
        embed.add_field(name="🔑 Clés disponibles", value=f"**{len(keys)}**", inline=True)
        embed.add_field(name="🎮 Jeux disponibles", value=f"**{jeux_list or 'Aucun'}**", inline=False)
        view = SteamKeyView(interaction_or_ctx.user.id)
        return await self._send(interaction_or_ctx, embed, view=view), view

    async def _try_win_key(self, interaction_or_ctx):
        keys_dispo = await self._get_all_steam_keys()
        user_id = str(interaction_or_ctx.user.id)
        reiatsu_points = await self._get_reiatsu(user_id)

        if reiatsu_points < REIATSU_COST:
            await self._send(interaction_or_ctx, discord.Embed(
                title="⛔ Pas assez de Reiatsu",
                description=f"Il te faut **{REIATSU_COST}** pour miser.",
                color=discord.Color.orange()
            ))
            return

        msg, view = await self._send_intro_embed(interaction_or_ctx, reiatsu_points, keys_dispo)
        await view.wait()
        if not view.value:
            return

        await self._update_reiatsu(user_id, reiatsu_points - REIATSU_COST)

        if keys_dispo and random.random() <= WIN_CHANCE:
            view_confirm = ConfirmKeyView(interaction_or_ctx.user.id, keys_dispo, msg, 0)
            await safe_edit(msg, embed=view_confirm.build_embed(), view=view_confirm)
            await view_confirm.wait()
            if view_confirm.choice == "accept":
                chosen = view_confirm.current_key
                await self._mark_steam_key_won(chosen["id"], interaction_or_ctx.user.name)
                try:
                    await interaction_or_ctx.user.send(f"🎁 **Clé Steam pour {chosen['game_name']}**\n`{chosen['steam_key']}`")
                    await safe_edit(msg, embed=discord.Embed(title="✅ Clé envoyée en DM !", color=discord.Color.green()), view=None)
                except discord.Forbidden:
                    await safe_edit(msg, embed=discord.Embed(title="⚠️ Impossible d'envoyer un DM.", color=discord.Color.orange()), view=None)
            elif view_confirm.choice == "reject":
                await safe_edit(msg, embed=discord.Embed(title="🔄 Clé laissée dispo pour les autres joueurs.", color=discord.Color.blurple()), view=None)
        else:
            await safe_edit(msg, embed=discord.Embed(
                title="Dommage !",
                description="❌ Tu n'as pas gagné cette fois, retente ta chance !",
                color=discord.Color.red()
            ), view=None)

    async def _send(self, interaction_or_ctx, embed, view=None):
        if isinstance(interaction_or_ctx, discord.Interaction):
            return await interaction_or_ctx.followup.send(embed=embed, view=view)
        return await safe_send(interaction_or_ctx.channel, embed=embed, view=view)

    @app_commands.command(name="steamkey", description="Miser des Reiatsu pour tenter de gagner une clé Steam")
    async def slash_steamkey(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._try_win_key(interaction)
        except Exception as e:
            print(f"[ERREUR /steamkey] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="steamkey", aliases=["sk"])
    async def prefix_steamkey(self, ctx: commands.Context):
        try:
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
