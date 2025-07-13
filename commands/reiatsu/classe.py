# ────────────────────────────────────────────────────────────────────────────────
# 📌 choisir_classe.py — Commande interactive !classe
# Objectif : Permettre aux joueurs de choisir leur classe Reiatsu via un menu déroulant
# Catégorie : VAACT
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, select
from supabase import create_client, Client
import os
import json

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Configuration Supabase
# ────────────────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ────────────────────────────────────────────────────────────────────────────────
# 📊 Données des classes Reiatsu
# ────────────────────────────────────────────────────────────────────────────────
with open("data/classes.json", "r", encoding="utf-8") as f:
    CLASSES = json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Vue du menu de sélection de classe
# ────────────────────────────────────────────────────────────────────────────────
class ClasseSelect(discord.ui.Select):
    def __init__(self, user_id):
        self.user_id = user_id
        options = [
            discord.SelectOption(
                label=classe,
                description=data["Passive"][:100],
                value=classe
            )
            for classe, data in CLASSES.items()
        ]
        super().__init__(placeholder="Choisis ta classe Reiatsu", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Tu ne peux pas choisir une classe pour un autre joueur.", ephemeral=True)
            return

        classe = self.values[0]
        user_id = str(interaction.user.id)

        try:
            supabase.table("reiatsu").update({"classe": classe}).eq("user_id", user_id).execute()
            embed = discord.Embed(
                title=f"✅ Classe choisie : {classe}",
                description=f"**Passive** : {CLASSES[classe]['Passive']}\n**Active** : {CLASSES[classe]['Active']}",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur lors de l'enregistrement : {e}", ephemeral=True)

class ClasseSelectView(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.add_item(ClasseSelect(user_id))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ChoisirClasse(commands.Cog):
    """
    Commande !classe — Choisir sa classe Reiatsu
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="classe",
        help="Choisir sa classe Reiatsu",
        description="Affiche un menu interactif pour choisir sa spécialisation Reiatsu."
    )
    async def classe(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🎭 Choisis ta classe Reiatsu",
            description="Sélectionne une classe dans le menu déroulant ci-dessous. Chaque classe possède une compétence passive et une active.",
            color=discord.Color.purple()
        )
        for nom, details in CLASSES.items():
            embed.add_field(
                name=f"🌀 {nom}",
                value=f"**Passive :** {details['Passive']}\n**Active :** {details['Active']}",
                inline=False
            )
        view = ClasseSelectView(ctx.author.id)
        await ctx.send(embed=embed, view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ChoisirClasse(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
