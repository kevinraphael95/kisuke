# ────────────────────────────────────────────────────────────────────────────────
# 📌 test_taches.py — Commande interactive !testtache
# Objectif : Proposer un mini-jeu via un menu interactif, gérer la sélection des tâches
# Catégorie : Général
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
from utils.discord_utils import safe_send, safe_edit, safe_respond  # ✅ Utilisation des safe_

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON des tâches
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "taches.json")

def load_tasks():
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Sélecteur principal des catégories de tâches
# ────────────────────────────────────────────────────────────────────────────────
class TaskCategorySelectView(View):
    def __init__(self, bot, tasks_data):
        super().__init__(timeout=120)
        self.bot = bot
        self.tasks_data = tasks_data
        self.add_item(TaskCategorySelect(self))

class TaskCategorySelect(Select):
    def __init__(self, parent_view: TaskCategorySelectView):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=cat, description=f"{len(self.parent_view.tasks_data[cat])} tâches") for cat in self.parent_view.tasks_data.keys()]
        super().__init__(placeholder="Choisis une catégorie de tâches", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_category = self.values[0]
        new_view = TaskSelectView(self.parent_view.bot, self.parent_view.tasks_data, selected_category)
        await safe_edit(
            interaction.message,
            content=f"Catégorie choisie : **{selected_category}**\nSélectionne maintenant une tâche :",
            embed=None,
            view=new_view
        )

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Sélecteur de tâches dans une catégorie
# ────────────────────────────────────────────────────────────────────────────────
class TaskSelectView(View):
    def __init__(self, bot, tasks_data, category):
        super().__init__(timeout=120)
        self.bot = bot
        self.tasks_data = tasks_data
        self.category = category
        self.add_item(TaskSelect(self))

class TaskSelect(Select):
    def __init__(self, parent_view: TaskSelectView):
        self.parent_view = parent_view
        tasks = self.parent_view.tasks_data[self.parent_view.category]
        options = [discord.SelectOption(label=task["name"], description=task.get("desc", "")) for task in tasks]
        super().__init__(placeholder="Choisis une tâche", options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.parent_view.category
        selected_task_name = self.values[0]
        task_list = self.parent_view.tasks_data[category]
        task = next((t for t in task_list if t["name"] == selected_task_name), None)

        if not task:
            await safe_respond(interaction, "❌ Tâche introuvable.")
            return

        embed = discord.Embed(
            title=f"Tâche : {task['name']}",
            description=task.get("desc", "Pas de description disponible."),
            color=discord.Color.blue()
        )
        # Ajout des détails complémentaires si présents
        if "details" in task:
            if isinstance(task["details"], dict):
                for k, v in task["details"].items():
                    value = "\n".join(v) if isinstance(v, list) else str(v)
                    embed.add_field(name=k.capitalize(), value=value, inline=False)
            else:
                embed.add_field(name="Détails", value=str(task["details"]), inline=False)

        await safe_edit(
            interaction.message,
            content=None,
            embed=embed,
            view=None
        )

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal — Commande !testtache
# ────────────────────────────────────────────────────────────────────────────────
class TestTache(commands.Cog):
    """
    Commande !testtache — Permet de lancer un mini-jeu interactif avec sélection de tâches.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="testtache",
        help="Lance un mini-jeu en choisissant une tâche.",
        description="Affiche un menu interactif pour choisir une catégorie et une tâche à réaliser."
    )
    async def testtache(self, ctx: commands.Context):
        """Commande principale avec menu interactif de sélection de tâches."""
        try:
            tasks_data = load_tasks()
            view = TaskCategorySelectView(self.bot, tasks_data)
            await safe_send(ctx.channel, "Choisis une catégorie de tâches :", view=view)
        except Exception as e:
            print(f"[ERREUR testtache] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors du chargement des tâches.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TestTache(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
