# ────────────────────────────────────────────────────────────────────────────────
# 📌 portes.py — Jeu des Portes interactif avec Supabase
# Objectif : Résoudre des énigmes et avancer dans les portes pour gagner du Reiatsu
# Catégorie : Jeux / Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond
from utils.supabase_client import supabase
import json
from pathlib import Path
import unicodedata

ENIGMES_PATH = Path("data/enigmes_portes.json")
with ENIGMES_PATH.open("r", encoding="utf-8") as f:
    ENIGMES = json.load(f)

# ───────────────────────────────────────────────────────────────────────────────
# 🔧 Fonction utilitaire pour normaliser les réponses
# ───────────────────────────────────────────────────────────────────────────────
def normalize(text: str) -> str:
    """Met en minuscules, enlève accents et espaces inutiles."""
    text = text.strip().lower()
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    return text

# ───────────────────────────────────────────────────────────────────────────────
# 🔘 Modal de réponse privée
# ───────────────────────────────────────────────────────────────────────────────
class ReponseModal(discord.ui.Modal):
    def __init__(self, cog, user, enigme):
        super().__init__(title=f"🔑 Réponse - {enigme['titre']}")
        self.cog = cog
        self.user = user
        self.enigme = enigme

        self.answer = discord.ui.TextInput(
            label="Ta réponse",
            placeholder="Entre ta réponse ici...",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.answer)

    async def on_submit(self, interaction: discord.Interaction):
        user_answer = normalize(self.answer.value)

        correct_answers = self.enigme["reponse"]
        if isinstance(correct_answers, str):
            correct_answers = [correct_answers]
        correct_answers = [normalize(ans) for ans in correct_answers]

        if user_answer in correct_answers:
            # ── Récupère la progression
            data = supabase.table("reiatsu_portes").select("*").eq("user_id", self.user.id).execute()
            current_door = data.data[0]["current_door"] if data.data else 1
            next_door = current_door + 1

            # ── Met à jour ou insère la porte
            if data.data:
                supabase.table("reiatsu_portes").update({
                    "current_door": next_door
                }).eq("user_id", self.user.id).execute()
            else:
                supabase.table("reiatsu_portes").insert({
                    "user_id": self.user.id,
                    "username": self.user.name,
                    "current_door": next_door
                }).execute()

            await interaction.response.send_message(
                f"✅ Bonne réponse ! Tu passes à la porte {next_door} 🚪", ephemeral=True
            )

            next_enigme = self.cog.get_enigme(next_door)
            if next_enigme:
                await self.cog.send_enigme_embed(self.user, interaction.channel, next_enigme)
        else:
            await interaction.response.send_message(
                "❌ Mauvaise réponse... Essaie encore !", ephemeral=True
            )

# ───────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ───────────────────────────────────────────────────────────────────────────────
class PortesGame(commands.Cog):
    """🎮 Jeu des Portes — Progression minimale"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_enigme(self, door_id: int):
        for e in ENIGMES:
            if e["id"] == door_id:
                return e
        return None

    async def send_enigme_embed(self, user: discord.User, channel, enigme):
        embed = discord.Embed(
            title=enigme["titre"],
            description=f"**Énigme :**\n{enigme['enigme']}",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Porte {enigme['id']}/{len(ENIGMES)} — Clique sur le bouton pour répondre.")

        view = discord.ui.View()
        button = discord.ui.Button(label="💬 Répondre", style=discord.ButtonStyle.primary)

        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != user.id:
                await interaction.response.send_message("⛔ Ce n’est pas ton tour.", ephemeral=True)
                return
            await interaction.response.send_modal(ReponseModal(self, user, enigme))

        button.callback = on_click
        view.add_item(button)

        await safe_send(channel, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────
    @app_commands.command(
        name="portes",
        description="Voir ou reprendre ta progression dans les portes"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_portes(self, interaction: discord.Interaction):
        user = interaction.user
        data = supabase.table("reiatsu_portes").select("*").eq("user_id", user.id).execute()
        current_door = data.data[0]["current_door"] if data.data else 1
        enigme = self.get_enigme(current_door)
        await safe_respond(interaction, f"🚪 {user.mention} commence ou reprend le Jeu des Portes !")
        if enigme:
            await self.send_enigme_embed(user, interaction.channel, enigme)

    # ────────────────────────────────────────────────────────────
    @commands.command(name="portes")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_portes(self, ctx: commands.Context):
        user = ctx.author
        data = supabase.table("reiatsu_portes").select("*").eq("user_id", user.id).execute()
        current_door = data.data[0]["current_door"] if data.data else 1
        enigme = self.get_enigme(current_door)
        await safe_send(ctx.channel, f"🚪 {user.mention} commence ou reprend le Jeu des Portes !")
        if enigme:
            await self.send_enigme_embed(user, ctx.channel, enigme)

# ───────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ───────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = PortesGame(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
