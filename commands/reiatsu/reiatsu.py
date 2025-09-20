# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu.py — Commande interactive /reiatsu et !reiatsu
# Objectif : Affiche le score Reiatsu et les infos d’un joueur
# Catégorie : Reiatsu
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur (centralisé dans bot.py)
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
from utils.discord_utils import safe_send, safe_edit, safe_respond, safe_defer  

# ────────────────────────────────────────────────────────────────────────────────
# 🛠 Helper : defer sécurisé
# ────────────────────────────────────────────────────────────────────────────────
async def safe_defer_if_needed(interaction: discord.Interaction):
    if not interaction.response.is_done():
        try:
            await interaction.response.defer()
        except Exception:
            pass

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "reiatsu.json")

def load_data():
    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {DATA_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Premier menu interactif
# ────────────────────────────────────────────────────────────────────────────────
class FirstSelectView(View):
    def __init__(self, bot, data):
        super().__init__(timeout=120)
        self.bot = bot
        self.data = data
        self.message: discord.Message | None = None
        self.add_item(FirstSelect(self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)

class FirstSelect(Select):
    def __init__(self, parent_view: FirstSelectView):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=key, value=key) for key in self.parent_view.data.keys()]
        super().__init__(placeholder="Sélectionne un joueur", options=options)

    async def callback(self, interaction: discord.Interaction):
        await safe_defer_if_needed(interaction)
        selected_key = self.values[0]
        infos = self.parent_view.data[selected_key]

        embed = discord.Embed(
            title=f"Infos Reiatsu pour {selected_key}",
            color=discord.Color.blue()
        )
        for field_name, field_value in infos.items():
            value = "\n".join(f"• {item}" for item in field_value) if isinstance(field_value, list) else str(field_value)
            embed.add_field(name=field_name.capitalize(), value=value, inline=False)

        await safe_edit(interaction.message, content=None, embed=embed, view=None)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Reiatsu(commands.Cog):
    """Commande /reiatsu et !reiatsu — Affiche les infos Reiatsu d’un membre"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_menu(self, channel: discord.abc.Messageable):
        data = load_data()
        if not data:
            await safe_send(channel, "❌ Impossible de charger les données.")
            return
        view = FirstSelectView(self.bot, data)
        view.message = await safe_send(channel, "Choisis un joueur :", view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="reiatsu",
        description="Affiche les informations Reiatsu d’un joueur."
    )
    @app_commands.checks.cooldown(rate=1, per=5.0, key=lambda i: i.user.id)
    async def slash_reiatsu(self, interaction: discord.Interaction):
        await safe_defer_if_needed(interaction)
        await self._send_menu(interaction.channel)
        try:
            await interaction.delete_original_response()
        except Exception:
            pass

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="reiatsu")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_reiatsu(self, ctx: commands.Context):
        await self._send_menu(ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Reiatsu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
