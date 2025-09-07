# ────────────────────────────────────────────────────────────────────────────────
# 📌 ace_bleach.py — Mini-jeu interactif Ace Attorney version Bleach
# Objectif : Permettre aux joueurs de choisir une histoire Bleach et de suivre un scénario
# Catégorie : Bleach
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
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

from utils.discord_utils import safe_send, safe_edit, safe_respond, safe_delete

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des histoires JSON (provisoire)
# ────────────────────────────────────────────────────────────────────────────────
STORIES_JSON_PATH = os.path.join("data", "ace_bleach_stories.json")

def load_stories():
    """Charge le fichier JSON contenant les histoires du mini-jeu."""
    try:
        with open(STORIES_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {STORIES_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Sélecteur d’histoire
# ────────────────────────────────────────────────────────────────────────────────
class StorySelectView(View):
    def __init__(self, bot, stories):
        super().__init__(timeout=120)
        self.bot = bot
        self.stories = stories
        self.message = None
        self.add_item(StorySelect(self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)

class StorySelect(Select):
    def __init__(self, parent_view: StorySelectView):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=title, value=title) for title in self.parent_view.stories.keys()]
        super().__init__(placeholder="Choisis une histoire Bleach", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_story = self.values[0]
        story_data = self.parent_view.stories[selected_story]

        embed = discord.Embed(
            title=f"📖 Histoire : {selected_story}",
            description=story_data.get("intro", "Pas d'introduction disponible."),
            color=discord.Color.orange()
        )

        await safe_edit(
            interaction.message,
            content=f"Tu as choisi : **{selected_story}**",
            embed=embed,
            view=None
        )

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class AceBleach(commands.Cog):
    """
    Commande /ace_bleach et !ace_bleach — Mini-jeu façon Ace Attorney avec l’univers Bleach
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_menu(self, channel: discord.abc.Messageable):
        stories = load_stories()
        if not stories:
            await safe_send(channel, "❌ Aucune histoire disponible.")
            return
        view = StorySelectView(self.bot, stories)
        view.message = await safe_send(channel, "Choisis ton histoire Bleach :", view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="ace_bleach",
        description="Lance le mini-jeu Ace Attorney version Bleach."
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.user.id))
    async def slash_ace_bleach(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._send_menu(interaction.channel)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s avant de rejouer.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /ace_bleach] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="ace_bleach")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_ace_bleach(self, ctx: commands.Context):
        try:
            await self._send_menu(ctx.channel)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s avant de rejouer.")
        except Exception as e:
            print(f"[ERREUR !ace_bleach] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = AceBleach(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
