# ────────────────────────────────────────────────────────────────────────────────
# 📌 flappy_bird.py — Commande interactive /flappy_bird et !flappy_bird
# Objectif : Jouer à Flappy Bird sur Discord avec obstacles, gravité et score
# Catégorie : Jeux
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
import random
import asyncio
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 UI — Vue interactive Flappy Bird Discord
# ────────────────────────────────────────────────────────────────────────────────
class FlappyBirdView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.width = 10             # largeur de la grille
        self.height = 5             # hauteur de la grille
        self.bird_y = 2             # position verticale du bird
        self.gravity = 1            # gravité descendante
        self.obstacles = []         # liste des colonnes de tuyaux
        self.score = 0
        self.game_over = False
        self.speed = 2              # temps entre chaque étape (s)
        self.message = None

        # Boutons
        self.add_item(UpButton(self))

        # Génération initiale des obstacles
        for _ in range(self.width):
            self.obstacles.append(self.generate_pipe())

    def generate_pipe(self):
        """Génère un tuyau vertical avec un trou aléatoire"""
        gap_start = random.randint(1, self.height - 2)
        pipe = []
        for y in range(self.height + 1):
            if y < gap_start or y > gap_start + 1:  # trou de taille 2
                pipe.append(y)
        return pipe

    def render_game(self):
        """Affiche la grille du jeu avec bird et tuyaux"""
        grid = ""
        for y in reversed(range(self.height + 1)):
            row = ""
            for x in range(self.width):
                if x == 1 and y == self.bird_y:
                    row += "🐦"
                elif y in self.obstacles[x]:
                    row += "🟩"
                else:
                    row += "⬛"
            grid += row + "\n"
        grid += f"Score : {self.score}"
        return grid

    async def step(self):
        """Fait avancer le jeu d’une étape"""
        if self.game_over:
            return

        # Bird descend
        if self.bird_y > 0:
            self.bird_y -= self.gravity

        # Défilement obstacles
        self.obstacles.pop(0)
        self.obstacles.append(self.generate_pipe())

        # Collision
        if self.bird_y in self.obstacles[1]:
            await safe_edit(self.message, content=f"💥 Game Over ! Score final : {self.score}", view=None)
            self.game_over = True
            self.stop()
            return

        # Incrément score
        self.score += 1
        await safe_edit(self.message, content=self.render_game(), view=self)

    async def start(self):
        """Lance le jeu automatique"""
        while not self.game_over:
            await self.step()
            await asyncio.sleep(self.speed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Bouton
# ────────────────────────────────────────────────────────────────────────────────
class UpButton(Button):
    def __init__(self, parent_view: FlappyBirdView):
        super().__init__(label="⬆️", style=discord.ButtonStyle.green)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.bird_y < self.parent_view.height:
            self.parent_view.bird_y += 1
        await self.parent_view.step()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class FlappyBird(commands.Cog):
    """Commande /flappy_bird et !flappy_bird — Mini-jeu interactif Flappy Bird"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _start_game(self, channel: discord.abc.Messageable):
        view = FlappyBirdView(self.bot)
        view.message = await safe_send(channel, view.render_game(), view=view)
        self.bot.loop.create_task(view.start())

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="flappy_bird",
        description="Joue à Flappy Bird sur Discord !"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_flappy_bird(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._start_game(interaction.channel)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /flappy_bird] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="flappy_bird")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_flappy_bird(self, ctx: commands.Context):
        try:
            await self._start_game(ctx.channel)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !flappy_bird] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = FlappyBird(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
