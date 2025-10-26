# ───────────────────────────────────────────────────────────────────────────────
# 📌 portes.py — Jeu des Portes interactif avec Supabase
# Objectif : Résoudre des énigmes et avancer dans les portes pour gagner du Reiatsu
# Catégorie : Jeux / Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ───────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond
from utils.supabase_client import supabase
import json
from pathlib import Path
import unicodedata

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Load the json
# ────────────────────────────────────────────────────────────────────────────────
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
            points = data.data[0]["points"] if data.data else 0
            next_door = current_door + 1

            # ── Récompense spéciale si c’est la dernière porte
            reward_message = ""
            if current_door == 100:
                points += 500
                reward_message = "🎉 Félicitations ! Tu as terminé toutes les portes et gagné **500 Reiatsu** !"

            # ── Met à jour ou insère la porte
            if data.data:
                supabase.table("reiatsu_portes").update({
                    "current_door": next_door,
                    "points": points
                }).eq("user_id", self.user.id).execute()
            else:
                supabase.table("reiatsu_portes").insert({
                    "user_id": self.user.id,
                    "username": self.user.name,
                    "current_door": next_door,
                    "points": points
                }).execute()

            await interaction.response.send_message(
                f"✅ Bonne réponse ! Tu passes à la porte {next_door} 🚪\n{reward_message}", ephemeral=True
            )

            # ── Envoi de la prochaine énigme si elle existe
            next_enigme = self.cog.get_enigme(next_door)
            if next_enigme and next_door <= 100:
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

    # ────────────────────────────────────────────────────────────
    # 📦 Envoi d'une énigme avec bouton de réponse
    # ────────────────────────────────────────────────────────────
    async def send_enigme_embed(self, user: discord.User, channel, enigme):
        embed = discord.Embed(
            title=enigme["titre"],
            description=f"**Énigme :**\n{enigme['enigme']}",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Porte {enigme['id']}/{len(ENIGMES)} — Clique sur le bouton pour répondre.")

        # ── Vue principale (comme dans mot_contraint)
        class ReponseView(discord.ui.View):
            def __init__(self, user, cog, enigme):
                super().__init__(timeout=None)
                self.user = user
                self.cog = cog
                self.enigme = enigme
                self.add_item(RepondreButton(self))

        # ── Bouton de réponse
        class RepondreButton(discord.ui.Button):
            def __init__(self, parent_view):
                super().__init__(label="💬 Répondre", style=discord.ButtonStyle.primary)
                self.parent_view = parent_view

            async def callback(self, interaction: discord.Interaction):
                if interaction.user.id != self.parent_view.user.id:
                    return await interaction.response.send_message("⛔ Ce n’est pas ton tour.", ephemeral=True)
                await interaction.response.send_modal(
                    ReponseModal(self.parent_view.cog, self.parent_view.user, self.parent_view.enigme)
                )

        view = ReponseView(user, self, enigme)
        message = await channel.send(embed=embed, view=view)
        view.message = message  # ← garde la référence comme dans mot_contraint

    # ────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
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
    # 🔹 Commande PREFIX
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
