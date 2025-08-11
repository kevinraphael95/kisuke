# ────────────────────────────────────────────────────────────────────────────────
# 📌 pizza.py — Commande interactive /pizza et !pizza
# Objectif : Générer une pizza aléatoire simple avec interaction slash et préfixe
# Catégorie : Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
import json
import os
import random
from utils.discord_utils import safe_send, safe_edit, safe_respond  # ✅ Utilisation des safe_

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "pizza_options.json")

def load_data():
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu interactif pour choisir type de pizza (exemple)
# ────────────────────────────────────────────────────────────────────────────────
class PizzaTypeSelect(Select):
    def __init__(self, parent_view: discord.ui.View, data):
        self.parent_view = parent_view
        self.data = data
        options = [
            discord.SelectOption(label=key, value=key)
            for key in data.keys()
        ]
        super().__init__(placeholder="Choisis un type de pizza", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        selected_type = self.values[0]
        # Générer une pizza aléatoire dans ce type
        options = self.data[selected_type]
        pate = random.choice(options["pates"])
        base = random.choice(options["bases"])
        fromage = random.choice(options["fromages"])
        garnitures = random.sample(options["garnitures"], k=min(2, len(options["garnitures"])))
        toppings = random.sample(options["toppings_speciaux"], k=min(1, len(options["toppings_speciaux"])))

        embed = discord.Embed(
            title=f"🍕 Pizza aléatoire : {selected_type}",
            color=discord.Color.orange()
        )
        embed.add_field(name="Pâte", value=pate, inline=False)
        embed.add_field(name="Base (sauce)", value=base, inline=False)
        embed.add_field(name="Fromage", value=fromage, inline=False)
        embed.add_field(name="Garnitures", value=", ".join(garnitures), inline=False)
        embed.add_field(name="Toppings spéciaux", value=", ".join(toppings), inline=False)

        # On enlève le menu pour éviter sélection multiple
        self.parent_view.clear_items()
        await safe_edit(interaction.message, embed=embed, view=self.parent_view)

class PizzaView(View):
    def __init__(self, bot, data):
        super().__init__(timeout=120)
        self.bot = bot
        self.data = data
        self.add_item(PizzaTypeSelect(self, data))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Pizza(commands.Cog):
    """
    Commande /pizza et !pizza — Génère une pizza aléatoire simple avec interaction
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ──────────────────────────────────────────────────────────────────────────────
    async def _send_menu(self, channel: discord.abc.Messageable):
        """Envoie le menu interactif de sélection du type de pizza."""
        data = load_data()
        view = PizzaView(self.bot, data)
        await safe_send(channel, "Choisis le type de pizza à générer :", view=view)

    # ──────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ──────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="pizza", description="Génère une pizza aléatoire.")
    async def slash_pizza(self, interaction: discord.Interaction):
        """Commande slash principale qui affiche le menu interactif."""
        try:
            await interaction.response.defer()
            await self._send_menu(interaction.channel)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /pizza] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue lors du chargement des données.", ephemeral=True)

    # ──────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ──────────────────────────────────────────────────────────────────────────────
    @commands.command(name="pizza")
    async def prefix_pizza(self, ctx: commands.Context):
        """Commande préfixe qui affiche le menu interactif."""
        try:
            await self._send_menu(ctx.channel)
        except Exception as e:
            print(f"[ERREUR !pizza] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors du chargement des données.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Pizza(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
