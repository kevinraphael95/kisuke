# ────────────────────────────────────────────────────────────────────────────────
# 📌 pizza_aléatoire.py — Commande interactive /pizza et !pizza
# Objectif : Générer une pizza aléatoire simple (pâte, sauce, fromage, garnitures, toppings)
# Catégorie : Fun&Random
# Accès : Tous
# Cooldown : 1 utilisation / 3 secondes / utilisateur (géré globalement dans bot.py)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, button
import json
import os
import random
from utils.discord_utils import safe_send, safe_edit, safe_respond, safe_defer

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "pizza_options.json")

def load_data():
    """Charge les options de pizza depuis le fichier JSON."""
    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {DATA_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Fonction commune pour générer l'embed pizza
# ────────────────────────────────────────────────────────────────────────────────
def generate_pizza_embed(data: dict) -> discord.Embed:
    """Génère un embed de pizza aléatoire."""
    pate = random.choice(data.get("pates", ["Classique"]))
    base = random.choice(data.get("bases", ["Tomate"]))
    fromage = random.choice(data.get("fromages", ["Mozzarella"]))
    garnitures_list = data.get("garnitures", ["Champignons", "Jambon"])
    garnitures = random.sample(garnitures_list, k=min(2, len(garnitures_list)))
    toppings_list = data.get("toppings_speciaux", ["Olives"])
    toppings = random.sample(toppings_list, k=1)

    embed = discord.Embed(
        title="🍕 Ta pizza aléatoire",
        color=discord.Color.orange()
    )
    embed.add_field(name="Pâte", value=pate, inline=False)
    embed.add_field(name="Base (sauce)", value=base, inline=False)
    embed.add_field(name="Fromage", value=fromage, inline=False)
    embed.add_field(name="Garnitures", value=", ".join(garnitures), inline=False)
    embed.add_field(name="Toppings spéciaux", value=", ".join(toppings), inline=False)
    embed.set_footer(text="🍕 Clique sur le bouton pour générer une nouvelle pizza.")
    return embed

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue interactive avec bouton "Nouvelle pizza"
# ────────────────────────────────────────────────────────────────────────────────
class PizzaView(View):
    """Vue contenant un bouton pour générer une nouvelle pizza."""
    def __init__(self, data: dict, author: discord.Member):
        super().__init__(timeout=60)
        self.data = data
        self.author = author
        self.message: discord.Message | None = None

    async def on_timeout(self):
        """Désactive le bouton quand la vue expire."""
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    @button(label="🍕 Nouvelle pizza", style=discord.ButtonStyle.green)
    async def nouvelle_pizza(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Régénère la pizza si c'est l'auteur qui clique sur le bouton."""
        if interaction.user != self.author:
            return await safe_respond(interaction, "❌ Tu ne peux pas utiliser ce bouton.", ephemeral=True)

        await safe_defer(interaction)
        new_embed = generate_pizza_embed(self.data)
        if self.message:
            await safe_edit(self.message, embed=new_embed, view=self)
        else:
            await safe_edit(interaction.message, embed=new_embed, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class PizzaAleatoire(commands.Cog):
    """Commande /pizza et !pizza — Génère une pizza aléatoire simple."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_pizza(self, channel: discord.abc.Messageable, author: discord.Member):
        """Envoie l'embed pizza avec la vue interactive."""
        data = load_data()
        if not data:
            await safe_send(channel, "❌ Impossible de charger les options de pizza.")
            return

        embed = generate_pizza_embed(data)
        view = PizzaView(data, author=author)
        view.message = await safe_send(channel, embed=embed, view=view)

    # 🔹 Commande PREFIX
    @commands.command(name="pizza", help="Génère une pizza aléatoire.")
    async def prefix_pizza(self, ctx: commands.Context):
        await self._send_pizza(ctx.channel, ctx.author)

    # 🔹 Commande SLASH
    @app_commands.command(name="pizza", description="Génère une pizza aléatoire.")
    async def slash_pizza(self, interaction: discord.Interaction):
        await self._send_pizza(interaction.channel, interaction.user)

# ────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = PizzaAleatoire(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun&Random"
    await bot.add_cog(cog)
