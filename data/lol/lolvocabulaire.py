# ────────────────────────────────────────────────────────────────────────────────
# 📌 vocabulaire.py — Commande interactive !voc
# Objectif : Consulter le vocabulaire de League of Legends
# Catégorie : LoL
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

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "vocabulaire_lol.json")

def load_data():
    """Charge le vocabulaire depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Vue de sélection des termes
# ────────────────────────────────────────────────────────────────────────────────
class VocabulaireSelectView(View):
    """Vue principale pour choisir un terme du vocabulaire."""
    def __init__(self, bot, data):
        super().__init__(timeout=120)
        self.bot = bot
        self.data = data
        self.add_item(VocabulaireSelect(self))

class VocabulaireSelect(Select):
    """Menu déroulant pour choisir un terme du vocabulaire."""
    def __init__(self, parent_view: VocabulaireSelectView):
        self.parent_view = parent_view
        options = [
            discord.SelectOption(label=terme, value=terme, description=data[:100])
            for terme, data in self.parent_view.data.items()
        ]
        super().__init__(placeholder="Choisis un terme de vocabulaire", options=options)

    async def callback(self, interaction: discord.Interaction):
        terme = self.values[0]
        definition = self.parent_view.data.get(terme, "Définition introuvable.")

        embed = discord.Embed(
            title=f"📘 Terme : {terme}",
            description=definition,
            color=discord.Color.dark_teal()
        )

        await interaction.response.edit_message(
            content=None,
            embed=embed,
            view=None
        )

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class VocabulaireLoL(commands.Cog):
    """
    Commande !voc — Consulte le vocabulaire de League of Legends
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="lolvocbulaire",
        aliases=["lolvoc"],
        help="Consulte un terme de vocabulaire de LoL.",
        description="Affiche la liste des termes de LoL et leur définition."
    )
    async def voc(self, ctx: commands.Context, *, terme: str = None):
        """Commande principale avec menu interactif ou recherche directe."""
        try:
            data = load_data()
            if terme:
                terme = terme.lower()
                match = next((k for k in data if k.lower() == terme), None)
                if match:
                    embed = discord.Embed(
                        title=f"📘 Terme : {match}",
                        description=data[match],
                        color=discord.Color.green()
                    )
                    await ctx.send(embed=embed)
                else:
                    await ctx.send("❌ Terme non trouvé dans le dictionnaire de LoL.")
            else:
                view = VocabulaireSelectView(self.bot, data)
                await ctx.send("📚 Voici la liste des termes disponibles :", view=view)
        except Exception as e:
            print(f"[ERREUR voc] {e}")
            await ctx.send("❌ Une erreur est survenue lors du chargement des données.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = VocabulaireLoL(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "LoL"
    await bot.add_cog(cog)
