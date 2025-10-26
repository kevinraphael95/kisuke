# ────────────────────────────────────────────────────────────────────────────────
# 📌 portes.py — Jeu des Portes interactif avec Supabase
# Objectif : Résoudre des énigmes et avancer dans les portes pour gagner du Reiatsu
# Catégorie : Jeux / Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Modal, TextInput, Button
from utils.discord_utils import safe_send, safe_respond, safe_edit
from utils.supabase_client import supabase
from pathlib import Path
import json, unicodedata

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Chargement des énigmes
# ────────────────────────────────────────────────────────────────────────────────
ENIGMES_PATH = Path("data/enigmes_portes.json")
with ENIGMES_PATH.open("r", encoding="utf-8") as f:
    ENIGMES = json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Fonction utilitaire : normalisation du texte
# ────────────────────────────────────────────────────────────────────────────────
def normalize(text: str) -> str:
    text = text.strip().lower()
    text = ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )
    return text

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Modal de réponse à une énigme
# ────────────────────────────────────────────────────────────────────────────────
class ReponseModal(Modal):
    def __init__(self, parent_view):
        super().__init__(title=f"🔑 Réponse - {parent_view.enigme['titre']}")
        self.parent_view = parent_view
        self.answer_input = TextInput(
            label="Ta réponse",
            placeholder="Entre ta réponse ici...",
            required=True
        )
        self.add_item(self.answer_input)

    async def on_submit(self, interaction: discord.Interaction):
        await self.parent_view.check_answer(interaction, self.answer_input.value.strip())

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Vue principale du jeu des portes
# ────────────────────────────────────────────────────────────────────────────────
class PortesView(View):
    def __init__(self, user: discord.User, enigme: dict, cog):
        super().__init__(timeout=None)
        self.user = user
        self.enigme = enigme
        self.cog = cog
        self.add_item(RepondreButton(self))

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.enigme["titre"],
            description=f"**Énigme :**\n{self.enigme['enigme']}",
            color=discord.Color.blurple()
        )
        embed.set_footer(
            text=f"Porte {self.enigme['id']}/{len(ENIGMES)} — Clique sur le bouton pour répondre."
        )
        return embed

    async def check_answer(self, interaction: discord.Interaction, answer: str):
        if interaction.user.id != self.user.id:
            return await safe_respond(interaction, "⛔ Ce n’est pas ton tour.", ephemeral=True)

        user_answer = normalize(answer)
        correct = self.enigme["reponse"]
        if isinstance(correct, str):
            correct = [correct]
        correct = [normalize(ans) for ans in correct]

        if user_answer in correct:
            data = supabase.table("reiatsu_portes").select("*").eq("user_id", self.user.id).execute()
            current_door = data.data[0]["current_door"] if data.data else 1
            points = data.data[0]["points"] if data.data else 0
            next_door = current_door + 1

            reward_message = ""
            if current_door == 100:
                points += 500
                reward_message = "🎉 Félicitations ! Tu as terminé toutes les portes et gagné **500 Reiatsu** !"

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

            await safe_respond(
                interaction,
                f"✅ Bonne réponse ! Tu passes à la porte {next_door} 🚪\n{reward_message}",
                ephemeral=True
            )

            next_enigme = self.cog.get_enigme(next_door)
            if next_enigme and next_door <= 100:
                await self.cog.send_enigme(interaction.channel, self.user, next_enigme)
        else:
            await safe_respond(interaction, "❌ Mauvaise réponse... Essaie encore !", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Bouton "Répondre"
# ────────────────────────────────────────────────────────────────────────────────
class RepondreButton(Button):
    def __init__(self, parent_view):
        super().__init__(label="💬 Répondre", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.user.id:
            return await safe_respond(interaction, "⛔ Ce n’est pas ton tour.", ephemeral=True)
        await interaction.response.send_modal(ReponseModal(self.parent_view))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class PortesGame(commands.Cog):
    """🎮 Jeu des Portes interactif — Résous les énigmes et avance dans ta progression !"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_enigme(self, door_id: int):
        for e in ENIGMES:
            if e["id"] == door_id:
                return e
        return None

    async def send_enigme(self, channel, user, enigme):
        view = PortesView(user, enigme, self)
        embed = view.build_embed()
        view.message = await safe_send(channel, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────
    @app_commands.command(
        name="portes",
        description="Jeu : résous des énigmes et passe les portes pour gagner du Reiatsu."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_portes(self, interaction: discord.Interaction):
        user = interaction.user
        data = supabase.table("reiatsu_portes").select("*").eq("user_id", user.id).execute()
        current_door = data.data[0]["current_door"] if data.data else 1
        enigme = self.get_enigme(current_door)
        await safe_respond(interaction, f"🚪 {user.mention} commence ou reprend le Jeu des Portes !")
        if enigme:
            await self.send_enigme(interaction.channel, user, enigme)

    # ────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────
    @commands.command(name="portes", help="Jeu : résous des énigmes et avance dans les portes.")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_portes(self, ctx: commands.Context):
        user = ctx.author
        data = supabase.table("reiatsu_portes").select("*").eq("user_id", user.id).execute()
        current_door = data.data[0]["current_door"] if data.data else 1
        enigme = self.get_enigme(current_door)
        await safe_send(ctx.channel, f"🚪 {user.mention} commence ou reprend le Jeu des Portes !")
        if enigme:
            await self.send_enigme(ctx.channel, user, enigme)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = PortesGame(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
