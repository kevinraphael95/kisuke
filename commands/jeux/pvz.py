# ────────────────────────────────────────────────────────────────────────────────
# 📌 mini_pvz_buttons.py — Mini-jeu Plants vs Zombies interactif
# Objectif : Placer des plantes sur une grille avec boutons et repousser les zombies
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import asyncio
import random

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class MiniPvZButtons(commands.Cog):
    """
    Commande /pvz et !pvz — Mini-jeu Plants vs Zombies avec boutons interactifs
    """
    GRID_ROWS = 3
    GRID_COLS = 5
    ZOMBIE_PROB = 0.3

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_games = {}  # user_id -> game_state

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="pvz",
        description="Joue à un mini Plants vs Zombies interactif !"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_pvz(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.start_game(interaction.user, interaction.channel)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="pvz")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_pvz(self, ctx: commands.Context):
        await self.start_game(ctx.author, ctx.channel)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Création et démarrage d'une partie
    # ────────────────────────────────────────────────────────────────────────────
    async def start_game(self, user, channel):
        if user.id in self.active_games:
            return await channel.send("❌ Tu as déjà une partie en cours !")

        state = {
            "grid": [[None for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)],
            "selected_plant": None,
            "zombies": [[] for _ in range(self.GRID_ROWS)],
            "turn": 0,
            "message": None,
            "running": True
        }
        self.active_games[user.id] = state

        view = self.create_game_view(user, state)
        msg = await channel.send("🌱 Mini PvZ", view=view)
        state["message"] = msg

        asyncio.create_task(self.game_loop(user, state))

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Création de la view du jeu (grille + plantes)
    # ────────────────────────────────────────────────────────────────────────────
    def create_game_view(self, user, state):
        class GridButton(Button):
            def __init__(self, row, col):
                super().__init__(label="⬜", style=discord.ButtonStyle.secondary)
                self.row = row
                self.col = col

            async def callback(inner_self, interaction: discord.Interaction):
                if interaction.user.id != user.id:
                    return await interaction.response.send_message("❌ Ce bouton n'est pas pour toi !", ephemeral=True)

                plant = state["selected_plant"]
                if plant and state["grid"][inner_self.row][inner_self.col] is None:
                    state["grid"][inner_self.row][inner_self.col] = plant
                    state["selected_plant"] = None  # désélectionne après placement
                    await inner_self.view.update_buttons(state)
                    await interaction.response.edit_message(view=inner_self.view)

        class PlantSelector(Button):
            def __init__(self, plant_name):
                super().__init__(label=plant_name, style=discord.ButtonStyle.secondary)
                self.plant_name = plant_name

            async def callback(inner_self, interaction: discord.Interaction):
                if interaction.user.id != user.id:
                    return await interaction.response.send_message("❌ Ce bouton n'est pas pour toi !", ephemeral=True)
                state["selected_plant"] = self.plant_name if state["selected_plant"] != self.plant_name else None
                await inner_self.view.update_buttons(state)
                await interaction.response.edit_message(view=inner_self.view)

        class PvZView(View):
            def __init__(self):
                super().__init__(timeout=None)
                self.grid_buttons = [[GridButton(r, c) for c in range(MiniPvZButtons.GRID_COLS)] for r in range(MiniPvZButtons.GRID_ROWS)]
                for row in self.grid_buttons:
                    for btn in row:
                        self.add_item(btn)
                self.plant_buttons = [PlantSelector(p) for p in ["Tournesol", "Tire-pois", "Noix"]]
                for btn in self.plant_buttons:
                    self.add_item(btn)

            async def update_buttons(self, state):
                # Met à jour la grille
                for r in range(MiniPvZButtons.GRID_ROWS):
                    for c in range(MiniPvZButtons.GRID_COLS):
                        plant = state["grid"][r][c]
                        zombie_here = c in state["zombies"][r]
                        if plant == "Tournesol":
                            label = "🌻"
                        elif plant == "Tire-pois":
                            label = "🌿"
                        elif plant == "Noix":
                            label = "🥥"
                        else:
                            label = "⬜"
                        if zombie_here:
                            label += "🧟"
                        self.grid_buttons[r][c].label = label
                        self.grid_buttons[r][c].style = discord.ButtonStyle.secondary
                # Met à jour les boutons plantes
                for btn in self.plant_buttons:
                    btn.style = discord.ButtonStyle.success if state["selected_plant"] == btn.plant_name else discord.ButtonStyle.secondary

        return PvZView()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Boucle principale du jeu
    # ────────────────────────────────────────────────────────────────────────────
    async def game_loop(self, user, state):
        while state["running"]:
            await asyncio.sleep(5)
            state["turn"] += 1
            # Zombies apparaissent
            for r in range(self.GRID_ROWS):
                if random.random() < self.ZOMBIE_PROB:
                    state["zombies"][r].append(self.GRID_COLS - 1)

            # Déplacement des zombies et vérification Game Over
            for r in range(self.GRID_ROWS):
                for i in range(len(state["zombies"][r])):
                    state["zombies"][r][i] -= 1
                if 0 in state["zombies"][r]:
                    state["running"] = False
                    await state["message"].edit(content="💀 Game Over ! Un zombie a envahi ton jardin !", view=None)
                    del self.active_games[user.id]
                    return

            # Attaque des Tire-pois
            for r in range(self.GRID_ROWS):
                for c in range(self.GRID_COLS):
                    plant = state["grid"][r][c]
                    if plant == "Tire-pois":
                        zombies = [z for z in state["zombies"][r] if z >= c]
                        if zombies:
                            state["zombies"][r].remove(min(zombies))

            # Mise à jour de la grille
            await state["message"].view.update_buttons(state)
            await state["message"].edit(view=state["message"].view)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MiniPvZButtons(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
