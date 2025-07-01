# ────────────────────────────────────────────────────────────────────────────────
# 📌 pizza_aléatoire.py — Commande !pizza
# Objectif : Générer une pizza aléatoire simple (pâte, sauce, fromage, garnitures, toppings)
# Catégorie : Test
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, button
import json
import os
import random

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "pizza_options.json")

def load_data():
    """Charge les options de pizza depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue avec bouton "🍕 Nouvelle pizza"
# ────────────────────────────────────────────────────────────────────────────────
class PizzaView(View):
    """Vue contenant un bouton pour générer une nouvelle pizza."""
    def __init__(self, data):
        super().__init__(timeout=60)
        self.data = data

    @button(label="🍕 Nouvelle pizza", style=discord.ButtonStyle.green)
    async def nouvelle_pizza(self, interaction: discord.Interaction, button: discord.ui.Button):
        pate = random.choice(self.data["pates"])
        base = random.choice(self.data["bases"])
        fromage = random.choice(self.data["fromages"])
        garnitures = random.sample(self.data["garnitures"], k=2)
        toppings = random.sample(self.data["toppings_speciaux"], k=1)

        embed = discord.Embed(
            title="🍕 Ta pizza aléatoire",
            color=discord.Color.orange()
        )
        embed.add_field(name="Pâte", value=pate, inline=False)
        embed.add_field(name="Base (sauce)", value=base, inline=False)
        embed.add_field(name="Fromage", value=fromage, inline=False)
        embed.add_field(name="Garnitures", value=", ".join(garnitures), inline=False)
        embed.add_field(name="Toppings spéciaux", value=", ".join(toppings), inline=False)

        await interaction.response.edit_message(embed=embed, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class PizzaAleatoire(commands.Cog):
    """
    Commande !pizza — Génère une pizza aléatoire simple
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="pizza",
        help="Génère une pizza aléatoire.",
        description="Affiche une pizza composée d'une pâte, d'une base, d'un fromage, de garnitures et de toppings spéciaux choisis aléatoirement."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # Anti-spam 3 secondes
    async def pizza(self, ctx: commands.Context):
        """Commande principale qui envoie une pizza aléatoire."""

        try:
            data = load_data()

            pate = random.choice(data["pates"])
            base = random.choice(data["bases"])
            fromage = random.choice(data["fromages"])
            garnitures = random.sample(data["garnitures"], k=2)
            toppings = random.sample(data["toppings_speciaux"], k=1)

            embed = discord.Embed(
                title="🍕 Ta pizza aléatoire",
                color=discord.Color.orange()
            )
            embed.add_field(name="Pâte", value=pate, inline=False)
            embed.add_field(name="Base (sauce)", value=base, inline=False)
            embed.add_field(name="Fromage", value=fromage, inline=False)
            embed.add_field(name="Garnitures", value=", ".join(garnitures), inline=False)
            embed.add_field(name="Toppings spéciaux", value=", ".join(toppings), inline=False)

            view = PizzaView(data)
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            print(f"[ERREUR pizza] {e}")
            await ctx.send("❌ Une erreur est survenue lors de la génération de la pizza.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = PizzaAleatoire(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
