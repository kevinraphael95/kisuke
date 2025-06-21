# ────────────────────────────────────────────────────────────────────────────────
# 📌 vocabulaire.py — Commande interactive !voc
# Objectif : Consulter un lexique de vocabulaire League of Legends
# Catégorie : LoL
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import json
import os
import math

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON (lexique)
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "lexique_lol.json")

def load_data():
    """Charge les données depuis le fichier JSON du lexique."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 📚 Classe de pagination pour lexique
# ────────────────────────────────────────────────────────────────────────────────
class LexiquePaginator(discord.ui.View):
    def __init__(self, data, per_page=25):
        super().__init__(timeout=120)
        self.data = list(data.items())
        self.per_page = per_page
        self.page = 0
        self.max_page = max(math.ceil(len(self.data) / self.per_page) - 1, 0)

        # Boutons de navigation
        self.prev_button = discord.ui.Button(label="⏪", style=discord.ButtonStyle.secondary)
        self.next_button = discord.ui.Button(label="⏩", style=discord.ButtonStyle.secondary)
        self.prev_button.callback = self.prev_page
        self.next_button.callback = self.next_page

        self.add_item(self.prev_button)
        self.add_item(self.next_button)

        # Initial update des boutons
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.page <= 0
        self.next_button.disabled = self.page >= self.max_page

    def create_embed(self):
        embed = discord.Embed(
            title=f"📚 Lexique — Page {self.page + 1} / {self.max_page + 1}",
            color=discord.Color.blurple()
        )
        start = self.page * self.per_page
        end = start + self.per_page
        for key, value in self.data[start:end]:
            alias_txt = f"\n_(Alias : {', '.join(value['aliases'])})_" if value.get("aliases") else ""
            embed.add_field(name=key, value=f"{value['definition']}{alias_txt}", inline=False)
        return embed

    async def prev_page(self, interaction: discord.Interaction):
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def next_page(self, interaction: discord.Interaction):
        if self.page < self.max_page:
            self.page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.create_embed(), view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class VocabulaireLoL(commands.Cog):
    """
    Commande !voc — Cherche un terme LoL ou affiche le lexique complet
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="lolvocabulaire",
        aliases=["lolvoc"],
        help="Cherche un terme du lexique League of Legends.",
        description="Ex : !voc adc ou !voc jgl — Sans argument, affiche tout le lexique."
    )
    async def voc(self, ctx: commands.Context, *, terme: str = None):
        """Commande principale pour consulter un terme ou l'intégralité du lexique."""
        try:
            data = load_data()

            # ───────────────🔍 Recherche d’un terme spécifique ───────────────
            if terme:
                terme = terme.lower()
                for key, value in data.items():
                    if terme == key.lower() or terme in [alias.lower() for alias in value.get("aliases", [])]:
                        embed = discord.Embed(
                            title=f"📘 Terme : {key}",
                            description=value["definition"],
                            color=discord.Color.green()
                        )
                        if "aliases" in value and value["aliases"]:
                            embed.add_field(name="🔁 Alias", value=", ".join(value["aliases"]), inline=False)
                        await ctx.send(embed=embed)
                        return

                await ctx.send("❌ Terme non trouvé dans le lexique.")
                return

            # ───────────────📚 Affichage complet du lexique avec pagination ───────────────
            paginator = LexiquePaginator(data)
            await ctx.send(embed=paginator.create_embed(), view=paginator)

        except Exception as e:
            print(f"[ERREUR voc] {e}")
            await ctx.send("❌ Une erreur est survenue lors du chargement du lexique.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = VocabulaireLoL(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "LoL"
    await bot.add_cog(cog)
