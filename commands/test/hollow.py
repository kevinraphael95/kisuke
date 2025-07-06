# ────────────────────────────────────────────────────────────────────────────────
# 📌 hollow.py — Commande interactive !hollow
# Objectif : Faire apparaître un Hollow, le joueur peut l’attaquer en dépensant 50 reiatsu
# Catégorie : Hollow
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import os
from supabase_client import supabase  # ton client Supabase déjà configuré

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Constantes
# ────────────────────────────────────────────────────────────────────────────────
HOLLOW_IMAGE_PATH = os.path.join("data", "hollows", "hollow0.jpg")
REIATSU_COST = 50

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Vue avec bouton d’attaque
# ────────────────────────────────────────────────────────────────────────────────
class HollowView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)  # timeout 60 secondes pour l’interaction
        self.author_id = author_id
        self.attacked = False

    @discord.ui.button(label=f"Attaquer ({REIATSU_COST} reiatsu)", style=discord.ButtonStyle.red)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Ce bouton n’est pas pour toi.", ephemeral=True)
            return

        if self.attacked:
            await interaction.response.send_message("⚠️ Tu as déjà attaqué ce Hollow.", ephemeral=True)
            return

        user_id = str(interaction.user.id)

        # Récupérer le score reiatsu
        resp = supabase.table("reiatsu").select("points").eq("user_id", user_id).execute()
        if not resp.data:
            await interaction.response.send_message("❌ Tu n’as pas de Reiatsu enregistré.", ephemeral=True)
            return

        points = resp.data[0].get("points", 0)
        if points < REIATSU_COST:
            await interaction.response.send_message(f"❌ Tu n’as pas assez de Reiatsu (il te faut {REIATSU_COST}).", ephemeral=True)
            return

        # Retirer les 50 points reiatsu
        new_points = points - REIATSU_COST
        update_resp = supabase.table("reiatsu").update({"points": new_points}).eq("user_id", user_id).execute()
        if update_resp.error:
            await interaction.response.send_message("⚠️ Une erreur est survenue lors de la mise à jour.", ephemeral=True)
            return

        self.attacked = True
        # Désactiver le bouton après attaque
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

        await interaction.response.send_message(f"🎉 Bravo {interaction.user.display_name}, tu as vaincu le Hollow en dépensant {REIATSU_COST} reiatsu !", ephemeral=False)


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal — HollowCommand
# ────────────────────────────────────────────────────────────────────────────────
class HollowCommand(commands.Cog):
    """Commande !hollow — Apparition d’un Hollow à attaquer avec 50 reiatsu."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="hollow",
        help="Fais apparaître un Hollow à attaquer en dépensant 50 reiatsu."
    )
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)  # anti-spam 10s
    async def hollow(self, ctx: commands.Context):
        # Vérifier que l'image existe
        if not os.path.isfile(HOLLOW_IMAGE_PATH):
            await ctx.send("❌ Image du Hollow introuvable.")
            return

        file = discord.File(HOLLOW_IMAGE_PATH, filename="hollow.jpg")
        embed = discord.Embed(
            title="👹 Un Hollow est apparu !",
            description="Attaque-le en dépensant 50 points de Reiatsu !",
            color=discord.Color.dark_red()
        )
        embed.set_image(url="attachment://hollow.jpg")
        embed.set_footer(text="Tu as 60 secondes pour attaquer.")

        view = HollowView(author_id=ctx.author.id)
        await ctx.send(embed=embed, file=file, view=view)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HollowCommand(bot)
    for command in cog.get_commands():
        command.category = "Test"
    await bot.add_cog(cog)
    
