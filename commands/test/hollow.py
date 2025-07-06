# ────────────────────────────────────────────────────────────────────────────────
# 📌 hollow.py — Commande interactive !hollow
# Objectif : Affiche un Hollow dans un embed et permet de le vaincre contre 50 reiatsu
# Catégorie : VAACT
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import os
from utils.supabase import supabase  # Assure-toi que ton wrapper est bien ici

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données Reiatsu (via Supabase)
# ────────────────────────────────────────────────────────────────────────────────
async def get_user_reiatsu(user_id: int) -> int | None:
    """Récupère la quantité de reiatsu d'un utilisateur depuis Supabase."""
    try:
        response = supabase.table("reiatsu").select("amount").eq("user_id", user_id).single().execute()
        return response.data["amount"] if response.data else None
    except Exception as e:
        print(f"[ERREUR get_user_reiatsu] {e}")
        return None

async def update_user_reiatsu(user_id: int, new_amount: int):
    """Met à jour la quantité de reiatsu d'un utilisateur dans Supabase."""
    try:
        supabase.table("reiatsu").update({"amount": new_amount}).eq("user_id", user_id).execute()
    except Exception as e:
        print(f"[ERREUR update_user_reiatsu] {e}")

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Bouton pour vaincre le Hollow
# ────────────────────────────────────────────────────────────────────────────────
class HollowView(View):
    """Vue contenant le bouton pour vaincre le Hollow."""
    def __init__(self, user_id: int):
        super().__init__(timeout=30)
        self.user_id = user_id

    @discord.ui.button(label="⚔️ Tuer le Hollow (50 Reiatsu)", style=discord.ButtonStyle.danger)
    async def tuer(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Ce Hollow ne t'appartient pas.", ephemeral=True)
            return

        reiatsu = await get_user_reiatsu(self.user_id)
        if reiatsu is None:
            await interaction.response.send_message("❌ Impossible de récupérer ton reiatsu.", ephemeral=True)
            return

        if reiatsu < 50:
            await interaction.response.send_message("💨 Tu n'as pas assez de Reiatsu pour tuer ce Hollow.", ephemeral=True)
            return

        await update_user_reiatsu(self.user_id, reiatsu - 50)
        await interaction.response.edit_message(content="☠️ Le Hollow a été vaincu !", embed=None, view=None)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Hollow(commands.Cog):
    """
    Commande !hollow — Fait apparaître un Hollow qu'on peut vaincre contre 50 reiatsu.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="hollow",
        help="Fait apparaître un Hollow à vaincre.",
        description="Fait apparaître un Hollow et permet de le tuer avec 50 reiatsu."
    )
    async def hollow(self, ctx: commands.Context):
        """Commande principale qui affiche un Hollow à vaincre."""
        image_path = os.path.join("data", "hollows", "hollow0.jpg")
        if not os.path.exists(image_path):
            await ctx.send("❌ Image du Hollow introuvable.")
            return

        try:
            embed = discord.Embed(
                title="Un Hollow est apparu !",
                description="Un Hollow menaçant vient d'apparaître dans la Soul Society... ⚠️",
                color=discord.Color.dark_red()
            )
            embed.set_image(url="attachment://hollow0.jpg")

            file = discord.File(image_path, filename="hollow0.jpg")
            view = HollowView(ctx.author.id)

            await ctx.send(embed=embed, file=file, view=view)
        except Exception as e:
            print(f"[ERREUR hollow] {e}")
            await ctx.send("❌ Une erreur est survenue lors de l'apparition du Hollow.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Hollow(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
