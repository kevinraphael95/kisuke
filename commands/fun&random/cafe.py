# ────────────────────────────────────────────────────────────────────────────────
# 📌 cafe.py — Mini-jeu interactif /cafe et !cafe
# Objectif : Crée ton café avec tous les ingrédients possibles comme un vrai barista
# Catégorie : 
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🍵 Ingrédients classés par type
# ────────────────────────────────────────────────────────────────────────────────
BASES = ["Café filtre", "Espresso", "Ristretto", "Café glacé"]
LAITS = ["Lait", "Lait d'amande", "Lait de soja", "Lait d'avoine", "Crème"]
SIROPS = ["Vanille", "Caramel", "Noisette", "Chocolat", "Menthe", "Framboise", "Coco", "Lavande", "Citron", "Gingembre"]
TOPPINGS = ["Chocolat râpé", "Cannelle", "Noix de muscade", "Caramel", "Chantilly", "Glace à la vanille", "Glace au chocolat"]
EXTRAS = ["Double shot", "Mousse de lait", "Extra espresso", "Sirop supplémentaire"]

ALL_INGREDIENTS = BASES + LAITS + SIROPS + TOPPINGS + EXTRAS

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
def get_coffee_name(selected):
    """
    Génère un nom réaliste pour le café selon les ingrédients.
    """
    name_parts = []

    # Base
    base = [i for i in selected if i in BASES]
    if base:
        name_parts.append(base[0])
    else:
        name_parts.append("Café")

    # Lait
    lait = [i for i in selected if i in LAITS]
    if lait:
        name_parts.append(f"avec {', '.join(lait)}")

    # Sirop
    sirops = [i for i in selected if i in SIROPS]
    if sirops:
        name_parts.append(f"aromatisé au {', '.join(sirops)}")

    # Toppings
    toppings = [i for i in selected if i in TOPPINGS]
    if toppings:
        name_parts.append(f"et garni de {', '.join(toppings)}")

    # Extras
    extras = [i for i in selected if i in EXTRAS]
    if extras:
        name_parts.append(f"(Extras : {', '.join(extras)})")

    return " | ".join(name_parts) if selected else "Eau chaude…"

# ────────────────────────────────────────────────────────────────────────────────
# 🖱️ Vue interactive avec boutons
# ────────────────────────────────────────────────────────────────────────────────
class CoffeeView(View):
    def __init__(self):
        super().__init__(timeout=180)  # 3 minutes max
        self.selected = []

        for ingredient in ALL_INGREDIENTS:
            button = Button(label=ingredient, style=discord.ButtonStyle.primary)
            button.callback = self.make_callback(ingredient)
            self.add_item(button)

        finish = Button(label="Terminer", style=discord.ButtonStyle.success)
        finish.callback = self.finish
        self.add_item(finish)

    def make_callback(self, ingredient):
        async def callback(interaction: discord.Interaction):
            if ingredient not in self.selected:
                self.selected.append(ingredient)
                await interaction.response.edit_message(
                    content=f"Ingrédients sélectionnés : {', '.join(self.selected)}",
                    view=self
                )
            else:
                await interaction.response.send_message(
                    "Tu as déjà ajouté cet ingrédient !", ephemeral=True
                )
        return callback

    async def finish(self, interaction: discord.Interaction):
        coffee_name = get_coffee_name(self.selected)
        await interaction.response.edit_message(
            content=f"☕ Voici ton café personnalisé : **{coffee_name}** !\nIngrédients : {', '.join(self.selected)}",
            view=None
        )
        self.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Cafe(commands.Cog):
    """
    Commande /cafe et !cafe — Crée ton café avec tous les ingrédients possibles
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🔹 Commande SLASH
    @app_commands.command(
        name="cafe",
        description="Crée ton café personnalisé avec tous les ingrédients possibles."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_cafe(self, interaction: discord.Interaction):
        view = CoffeeView()
        await safe_respond(interaction, "Choisis tes ingrédients :", view=view)

    # 🔹 Commande PREFIX
    @commands.command(name="cafe")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_cafe(self, ctx: commands.Context):
        view = CoffeeView()
        await safe_send(ctx.channel, "Choisis tes ingrédients :", view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Cafe(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Random&Fun"
    await bot.add_cog(cog)
