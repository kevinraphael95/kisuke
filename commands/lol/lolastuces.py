# ────────────────────────────────────────────────────────────────────────────────
# 📌 astuces_lol.py — Commande interactive !astuce
# Objectif : Afficher une astuce League of Legends aléatoire avec bouton pour en changer
# Catégorie : LoL
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os
import random

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON (liste simple d'astuces)
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "lol", "astuces.json")

def load_data():
    """Charge les données depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Vue avec bouton pour nouvelle astuce
# ────────────────────────────────────────────────────────────────────────────────
class AstuceView(View):
    def __init__(self, bot, astuces):
        super().__init__(timeout=120)
        self.bot = bot
        self.astuces = astuces
        self.current_astuce = random.choice(self.astuces)
        self.nouveau_bouton = Button(label="Nouvelle astuce", style=discord.ButtonStyle.primary)
        self.nouveau_bouton.callback = self.nouvelle_astuce_callback
        self.add_item(self.nouveau_bouton)

    async def nouvelle_astuce_callback(self, interaction: discord.Interaction):
        self.current_astuce = random.choice(self.astuces)
        embed = discord.Embed(
            title="💡 Astuce League of Legends",
            description=self.current_astuce,
            color=discord.Color.gold()
        )
        await interaction.response.edit_message(embed=embed, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class AstucesLoL(commands.Cog):
    """
    Commande !astuce — Affiche une astuce LoL aléatoire avec bouton pour en changer.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="lolastuce",
        help="Affiche une astuce LoL aléatoire avec un bouton pour en changer.",
        description="Ex : !astuce — Affiche une astuce aléatoire, et tu peux cliquer sur le bouton pour une autre."
    )
    async def astuce(self, ctx: commands.Context):
        """Commande principale avec bouton interactif."""
        try:
            astuces = load_data()
            if not astuces:
                await ctx.send("❌ Aucune astuce trouvée.")
                return

            view = AstuceView(self.bot, astuces)
            embed = discord.Embed(
                title="💡 Astuce League of Legends",
                description=view.current_astuce,
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            print(f"[ERREUR astuce] {e}")
            await ctx.send("❌ Une erreur est survenue lors du chargement des astuces.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = AstucesLoL(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "LoL"
    await bot.add_cog(cog)
