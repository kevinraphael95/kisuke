# ────────────────────────────────────────────────────────────────────────────────
# 📌 cafe.py — Mini-jeu interactif /cafe et !cafe
# Objectif : Crée ton café personnalisé avec tous les ingrédients possibles ☕
# Catégorie : Random&Fun
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
INGREDIENT_CATEGORIES = {
    "☕ Bases": ["Café filtre", "Espresso", "Ristretto", "Café glacé", "Cold brew", "Cappuccino", "Latte", "Macchiato"],
    "🥛 Laits": ["Lait entier", "Lait écrémé", "Lait d’amande", "Lait de soja", "Lait d’avoine", "Lait de coco", "Crème", "Crème fouettée"],
    "🍯 Sirops": ["Vanille", "Caramel", "Noisette", "Chocolat", "Menthe", "Framboise", "Coco", "Lavande", "Citron", "Érable", "Cannelle"],
    "🍫 Toppings": ["Chocolat râpé", "Cannelle", "Noix de muscade", "Caramel", "Chantilly", "Glace à la vanille", "Glace au chocolat", "Éclats de cookies"],
    "⚡ Extras": ["Double shot", "Mousse de lait", "Extra espresso", "Sirop supplémentaire", "Décaféiné", "Sucre brun", "Sucre blanc", "Miel", "Glaçons"]
}

CATEGORY_LIST = list(INGREDIENT_CATEGORIES.keys())

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
def get_coffee_name(selected):
    """
    Génère un nom fun et cohérent pour le café selon les ingrédients.
    """
    if not selected:
        return "Eau chaude décevante 🫠"

    name = ""
    if any(b in selected for b in INGREDIENT_CATEGORIES["☕ Bases"]):
        base = next(b for b in selected if b in INGREDIENT_CATEGORIES["☕ Bases"])
        name += base
    else:
        name += "Café"

    sirop = [s for s in selected if s in INGREDIENT_CATEGORIES["🍯 Sirops"]]
    lait = [l for l in selected if l in INGREDIENT_CATEGORIES["🥛 Laits"]]
    toppings = [t for t in selected if t in INGREDIENT_CATEGORIES["🍫 Toppings"]]
    extras = [e for e in selected if e in INGREDIENT_CATEGORIES["⚡ Extras"]]

    if lait:
        name += f" au {lait[0]}"
    if sirop:
        name += f" aromatisé {sirop[0]}"
    if toppings:
        name += f" avec {toppings[0]}"
    if extras:
        name += f" ({extras[0]})"

    return name

# ────────────────────────────────────────────────────────────────────────────────
# 🖱️ Vue interactive multi-pages
# ────────────────────────────────────────────────────────────────────────────────
class CoffeeView(View):
    def __init__(self):
        super().__init__(timeout=180)
        self.selected = []
        self.page = 0
        self.refresh_page()

    def refresh_page(self):
        """Reconstruit les boutons de la page actuelle."""
        self.clear_items()
        category = CATEGORY_LIST[self.page]
        ingredients = INGREDIENT_CATEGORIES[category]

        for ingredient in ingredients:
            style = discord.ButtonStyle.primary if ingredient not in self.selected else discord.ButtonStyle.success
            button = Button(label=ingredient, style=style)
            button.callback = self.make_callback(ingredient)
            self.add_item(button)

        # Navigation
        if self.page > 0:
            prev = Button(label="◀️", style=discord.ButtonStyle.secondary)
            prev.callback = self.prev_page
            self.add_item(prev)

        if self.page < len(CATEGORY_LIST) - 1:
            nextb = Button(label="▶️", style=discord.ButtonStyle.secondary)
            nextb.callback = self.next_page
            self.add_item(nextb)

        # Terminer
        finish = Button(label="Terminer ☕", style=discord.ButtonStyle.success)
        finish.callback = self.finish
        self.add_item(finish)

    def make_callback(self, ingredient):
        async def callback(interaction: discord.Interaction):
            if ingredient in self.selected:
                self.selected.remove(ingredient)
            else:
                self.selected.append(ingredient)
            self.refresh_page()
            await interaction.response.edit_message(
                content=self.get_display_text(),
                view=self
            )
        return callback

    async def prev_page(self, interaction: discord.Interaction):
        self.page -= 1
        self.refresh_page()
        await interaction.response.edit_message(
            content=self.get_display_text(),
            view=self
        )

    async def next_page(self, interaction: discord.Interaction):
        self.page += 1
        self.refresh_page()
        await interaction.response.edit_message(
            content=self.get_display_text(),
            view=self
        )

    async def finish(self, interaction: discord.Interaction):
        name = get_coffee_name(self.selected)
        await interaction.response.edit_message(
            content=f"☕ Voici ton café personnalisé : **{name}**\n\nIngrédients : {', '.join(self.selected)}",
            view=None
        )
        self.stop()

    def get_display_text(self):
        category = CATEGORY_LIST[self.page]
        return f"**Catégorie : {category}**\nSélectionne tes ingrédients !\n\nActuellement : {', '.join(self.selected) if self.selected else 'Aucun'}"

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Cafe(commands.Cog):
    """
    Commande /cafe et !cafe — Crée ton café avec tous les ingrédients possibles
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="cafe",
        description="Crée ton café personnalisé avec des dizaines d’ingrédients ☕"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_cafe(self, interaction: discord.Interaction):
        view = CoffeeView()
        await safe_respond(interaction, view.get_display_text(), view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="cafe")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_cafe(self, ctx: commands.Context):
        view = CoffeeView()
        await safe_send(ctx.channel, view.get_display_text(), view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Cafe(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun&Random"
    await bot.add_cog(cog)
