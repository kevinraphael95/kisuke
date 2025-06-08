# ────────────────────────────────────────────────────────────────────────────────
# 📌 pizza.py — Commande interactive !pizza
# Objectif : Crée une pizza aléatoire à partir d'ingrédients variés
# Catégorie : Test
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
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "pizza_data.json")

def load_data():
    """Charge les ingrédients de pizza depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Bouton pour générer une pizza aléatoire
# ────────────────────────────────────────────────────────────────────────────────
class PizzaView(View):
    """Vue avec un bouton pour générer une pizza."""
    def __init__(self, bot, data):
        super().__init__(timeout=120)
        self.bot = bot
        self.data = data
        self.add_item(PizzaButton(self))

class PizzaButton(Button):
    """Bouton pour générer une pizza."""
    def __init__(self, parent_view: PizzaView):
        super().__init__(label="🍕 Générer une pizza", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        ingredients = self.parent_view.data
        pizza = {
            "Base": random.choice(ingredients["bases"]),
            "Sauce": random.choice(ingredients["sauces"]),
            "Fromage": random.choice(ingredients["fromages"]),
            "Garnitures": random.sample(ingredients["garnitures"], 2),
            "Toppings spéciaux": random.choice(ingredients["toppings"])
        }

        embed = discord.Embed(
            title="🍕 Ta pizza personnalisée est prête !",
            color=discord.Color.orange()
        )
        for k, v in pizza.items():
            if isinstance(v, list):
                value = "\n".join(f"• {item}" for item in v)
            else:
                value = f"• {v}"
            embed.add_field(name=k, value=value, inline=False)

        await interaction.response.edit_message(embed=embed, view=self.parent_view)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Pizza(commands.Cog):
    """
    Commande !pizza — Crée une pizza aléatoire
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="pizza",
        help="Génère une pizza aléatoire.",
        description="Génère une pizza aléatoire avec base, sauce, fromage, garnitures et toppings."
    )
    async def pizza(self, ctx: commands.Context):
        """Commande principale !pizza"""
        try:
            data = load_data()
            view = PizzaView(self.bot, data)
            await ctx.send("Appuie sur le bouton pour créer ta pizza :", view=view)
        except Exception as e:
            print(f"[ERREUR pizza] {e}")
            await ctx.send("❌ Une erreur est survenue lors du chargement des données.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Pizza(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
