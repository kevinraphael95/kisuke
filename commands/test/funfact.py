# ────────────────────────────────────────────────────────────────────────────────
# 📌 funfact_bleach.py — Commande interactive !funfact
# Objectif : Donne un fun fact sur Bleach
# Catégorie : 🧠 Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Select
import json
import os
import random

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "funfacts_bleach.json")

def load_data():
    """Charge les fun facts depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Vue avec bouton pour un fun fact aléatoire
# ────────────────────────────────────────────────────────────────────────────────
class FunFactView(View):
    """Vue contenant un bouton pour afficher un autre fun fact."""
    def __init__(self, facts):
        super().__init__(timeout=60)
        self.facts = facts

    @discord.ui.button(label="🔁 Autre fun fact", style=discord.ButtonStyle.blurple)
    async def new_fact_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        fact = random.choice(self.facts)
        await interaction.response.edit_message(content=f"🧠 **Fun Fact Bleach :** {fact}", view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class FunFactBleach(commands.Cog):
    """
    Commande !funfact — Donne un fun fact sur Bleach.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="funfact",
        help="🧠 Donne un fun fact sur Bleach.",
        description="Affiche un fait intéressant aléatoire tiré d'un fichier JSON."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def funfact(self, ctx: commands.Context):
        """Commande principale qui envoie un fun fact aléatoire avec un bouton pour en voir d'autres."""
        try:
            facts = load_data()
            if not facts:
                await ctx.send("❌ Aucun fun fact disponible.")
                return

            fact = random.choice(facts)
            view = FunFactView(facts)
            await ctx.send(f"🧠 **Fun Fact Bleach :** {fact}", view=view)

        except FileNotFoundError:
            await ctx.send("❌ Fichier `funfacts_bleach.json` introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : {e}")

    def cog_load(self):
        self.funfact.category = "Fun"

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = FunFactBleach(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
