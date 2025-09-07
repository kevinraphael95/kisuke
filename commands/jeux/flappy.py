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
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 UI — Vue interactive du jeu Flappy Bird
# ────────────────────────────────────────────────────────────────────────────────
class FlappyBirdView(View):
    def __init__(self, bot):
        super().__init__(timeout=None)  # on gère le timeout via self.stop()
        self.bot = bot
        self.bird_pos = 2
        self.max_height = 4
        self.min_height = 0
        self.width = 8
        self.obstacles = [self.generate_obstacle() for _ in range(self.width)]
        self.score = 0
        self.message = None
        self.running = True

        # Boutons pour contrôler le bird
        self.add_item(UpButton(self))
        self.add_item(DownButton(self))

    def generate_obstacle(self):
        """Crée un obstacle aléatoire avec un trou"""
        gap = random.randint(1, self.max_height - 1)
        return [i for i in range(self.max_height + 1) if i != gap]

    def render_game(self):
        """Affiche le terrain, le bird et les obstacles"""
        grid = ""
        for y in reversed(range(self.max_height + 1)):
            row = ""
            for x in range(self.width):
                if x == 1 and y == self.bird_pos:
                    row += "🐦"
                elif y in self.obstacles[x]:
                    row += "🟩"
                else:
                    row += "⬛"
            grid += row + "\n"
        grid += f"Score : {self.score}"
        return grid

    async def game_step(self):
        """Fait avancer le jeu d'une étape"""
        if not self.running:
            return

        # Gravité : bird descend
        if self.bird_pos > self.min_height:
            self.bird_pos -= 1

        # Décale obstacles
        self.obstacles.pop(0)
        self.obstacles.append(self.generate_obstacle())

        # Vérifie collision
        if self.bird_pos in self.obstacles[0]:
            await safe_edit(self.message, content=f"💥 Collision ! Score final : {self.score}", view=None)
            self.running = False
            self.stop()
            return

        # Incrémente le score
        self.score += 1
        await safe_edit(self.message, content=self.render_game(), view=self)

    async def start_game(self):
        """Lance le jeu automatique avec gravité et obstacles"""
        while self.running:
            await self.game_step()
            await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=2))

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Boutons
# ────────────────────────────────────────────────────────────────────────────────
class UpButton(Button):
    def __init__(self, parent_view: FlappyBirdView):
        super().__init__(label="⬆️", style=discord.ButtonStyle.green)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.bird_pos < self.parent_view.max_height:
            self.parent_view.bird_pos += 1
        await self.parent_view.game_step()

class DownButton(Button):
    def __init__(self, parent_view: FlappyBirdView):
        super().__init__(label="⬇️", style=discord.ButtonStyle.red)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.bird_pos > self.parent_view.min_height:
            self.parent_view.bird_pos -= 1
        await self.parent_view.game_step()

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
        self.bot.loop.create_task(view.start_game())

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
