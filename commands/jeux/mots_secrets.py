# ────────────────────────────────────────────────────────────────────────────────
# 📌 motssecrets.py — Jeu des Mots Secrets interactif avec Supabase
# Objectif : Trouver des mots pour gagner du Reiatsu
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

MOTS_PATH = Path("data/motssecrets.json")
with MOTS_PATH.open("r", encoding="utf-8") as f:
    MOTS = json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🔘 Modal de réponse privée
# ────────────────────────────────────────────────────────────────────────────────
class MotSecretModal(discord.ui.Modal):
    def __init__(self, cog, user):
        super().__init__(title="🔑 Propose ton mot secret")
        self.cog = cog
        self.user = user

        self.mot_input = discord.ui.TextInput(
            label="Ton mot",
            placeholder="Entre un mot à deviner...",
            style=discord.TextStyle.short,
            required=True
        )
        self.add_item(self.mot_input)

    async def on_submit(self, interaction: discord.Interaction):
        mot = self.mot_input.value.strip().lower()

        # ── Vérifie si le mot existe
        mot_data = [m for m in MOTS if m["mot"].lower() == mot]
        if not mot_data:
            await interaction.response.send_message("❌ Ce mot n'existe pas dans la liste.", ephemeral=True)
            return

        mot_id = mot_data[0]["id"]

        # ── Vérifie si l'utilisateur a déjà trouvé ce mot
        found = supabase.table("mots_trouves").select("*").eq("user_id", self.user.id).eq("mot_id", mot_id).execute()
        if found.data:
            await interaction.response.send_message("⚠️ Tu as déjà trouvé ce mot !", ephemeral=True)
            return

        # ── Ajoute dans mots_trouves
        supabase.table("mots_trouves").insert({"user_id": self.user.id, "mot_id": mot_id}).execute()

        # ── Donne 10 Reiatsu
        user_data = supabase.table("reiatsu").select("points").eq("user_id", self.user.id).execute()
        points = user_data.data[0]["points"] if user_data.data else 0
        supabase.table("reiatsu").update({"points": points + 10}).eq("user_id", self.user.id).execute()

        await interaction.response.send_message("✅ Bravo ! +10 Reiatsu !", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class MotsSecretsGame(commands.Cog):
    """
    🎮 Jeu des Mots Secrets — Trouve les mots pour gagner du Reiatsu
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_modal(self, user, channel):
        view = discord.ui.View()
        button = discord.ui.Button(label="💬 Proposer un mot", style=discord.ButtonStyle.primary)

        async def on_click(interaction: discord.Interaction):
            if interaction.user.id != user.id:
                await interaction.response.send_message("⛔ Ce n’est pas ton tour.", ephemeral=True)
                return
            await interaction.response.send_modal(MotSecretModal(self, user))

        button.callback = on_click
        view.add_item(button)

        await safe_send(channel, f"📝 {user.mention}, clique sur le bouton pour proposer un mot secret.", view=view)

    # ────────────────────────────────────────────────────────────
    @app_commands.command(
        name="motssecrets",
        description="Propose un mot secret pour gagner du Reiatsu !"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_motssecrets(self, interaction: discord.Interaction):
        await safe_respond(interaction, "📝 Lance ton mot secret !")
        await self.send_modal(interaction.user, interaction.channel)

    # ────────────────────────────────────────────────────────────
    @commands.command(name="motssecrets")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_motssecrets(self, ctx: commands.Context):
        await safe_send(ctx.channel, f"📝 {ctx.author.mention}, lance ton mot secret !")
        await self.send_modal(ctx.author, ctx.channel)

# ────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ───────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MotsSecretsGame(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
