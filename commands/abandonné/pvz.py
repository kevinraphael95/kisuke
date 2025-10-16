# ────────────────────────────────────────────────────────────────────────────────
# 📌 mini_pvz.py — Mini-jeu Plants vs Zombies
# Objectif : Placer des plantes sur une grille et repousser les zombies
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
class MiniPvZ(commands.Cog):
    """
    Commande /pvz et !pvz — Mini-jeu Plants vs Zombies interactif
    """
    GRID_ROWS = 3
    GRID_COLS = 5
    ZOMBIE_PROB = 0.3   # Probabilité d'apparition d'un zombie par tour

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_games = {}  # user_id -> game_state

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="pvz",
        description="Joue à un mini Plants vs Zombies !"
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

        # Initialisation de l'état du jeu
        state = {
            "grid": [[None for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)],
            "selected_plant": None,
            "zombies": [[] for _ in range(self.GRID_ROWS)],
            "turn": 0,
            "message": None,
            "running": True
        }
        self.active_games[user.id] = state

        # Affichage initial
        view = self.create_game_view(user, state)
        embed = self.render_grid(state)
        msg = await channel.send(embed=embed, view=view)
        state["message"] = msg

        # Boucle du jeu
        asyncio.create_task(self.game_loop(user, state))

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Création de la vue complète (grille + plantes)
    # ────────────────────────────────────────────────────────────────────────────
    def create_game_view(self, user, state):
        view = View(timeout=None)

        # Boutons de la grille
        for r in range(self.GRID_ROWS):
            for c in range(self.GRID_COLS):
                btn = self.GridButton(r, c, user, state)
                view.add_item(btn)

        # Boutons des plantes (en bas)
        for plant in ["Tournesol", "Tire-pois", "Noix"]:
            btn = self.PlantSelectorButton(plant, user, state)
            view.add_item(btn)

        return view

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Bouton de sélection de plante
    # ────────────────────────────────────────────────────────────────────────────
    class PlantSelectorButton(Button):
        def __init__(self, plant_name, user, state):
            super().__init__(label=plant_name, style=discord.ButtonStyle.secondary)
            self.plant_name = plant_name
            self.user = user
            self.state = state

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message("❌ Ce bouton n'est pas pour toi !", ephemeral=True)

            # Toggle sélection
            if self.state["selected_plant"] == self.plant_name:
                self.state["selected_plant"] = None
            else:
                self.state["selected_plant"] = self.plant_name

            # Mise à jour des couleurs
            for b in self.view.children:
                if isinstance(b, Button) and b.label in ["Tournesol", "Tire-pois", "Noix"]:
                    b.style = discord.ButtonStyle.success if b.label == self.state["selected_plant"] else discord.ButtonStyle.secondary

            await interaction.response.edit_message(view=self.view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Bouton de la grille pour placer une plante
    # ────────────────────────────────────────────────────────────────────────────
    class GridButton(Button):
        def __init__(self, row, col, user, state):
            super().__init__(label="⬜", style=discord.ButtonStyle.secondary, row=row)
            self.row = row
            self.col = col
            self.user = user
            self.state = state

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message("❌ Ce bouton n'est pas pour toi !", ephemeral=True)

            plant = self.state["selected_plant"]
            if not plant:
                return await interaction.response.send_message("❌ Sélectionne d'abord une plante !", ephemeral=True)

            if self.state["grid"][self.row][self.col] is None:
                self.state["grid"][self.row][self.col] = plant
                self.state["selected_plant"] = None
                # Désélectionne toutes les plantes
                for b in self.view.children:
                    if isinstance(b, Button) and b.label in ["Tournesol", "Tire-pois", "Noix"]:
                        b.style = discord.ButtonStyle.secondary
                await interaction.response.edit_message(embed=self.state["message"].embeds[0], view=self.view)
            else:
                await interaction.response.send_message("❌ Case déjà occupée !", ephemeral=True)

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

            # Déplacer les zombies
            for r in range(self.GRID_ROWS):
                for i in range(len(state["zombies"][r])):
                    state["zombies"][r][i] -= 1
                if 0 in state["zombies"][r]:
                    state["running"] = False
                    await state["message"].edit(
                        embed=discord.Embed(title="💀 Game Over!", description="Un zombie a envahi ton jardin !", color=discord.Color.red()),
                        view=None
                    )
                    del self.active_games[user.id]
                    return

            # Attaque des plantes
            for r in range(self.GRID_ROWS):
                for c in range(self.GRID_COLS):
                    plant = state["grid"][r][c]
                    if plant == "Tire-pois":
                        zombies = [z for z in state["zombies"][r] if z >= c]
                        if zombies:
                            state["zombies"][r].remove(min(zombies))

            # Mise à jour du message
            embed = self.render_grid(state)
            await state["message"].edit(embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Rendu de la grille en embed
    # ────────────────────────────────────────────────────────────────────────────
    def render_grid(self, state):
        rows = []
        for r in range(self.GRID_ROWS):
            row = ""
            for c in range(self.GRID_COLS):
                plant = state["grid"][r][c]
                zombie = c in state["zombies"][r]
                if plant == "Tournesol":
                    cell = "🌻"
                elif plant == "Tire-pois":
                    cell = "🌿"
                elif plant == "Noix":
                    cell = "🥥"
                else:
                    cell = "⬜"
                if zombie:
                    cell += "🧟"
                row += cell
            rows.append(row)
        embed = discord.Embed(title="🌱 Mini PvZ", description="\n".join(rows), color=discord.Color.green())
        if state["selected_plant"]:
            embed.set_footer(text=f"Plante sélectionnée : {state['selected_plant']}")
        return embed

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MiniPvZ(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
