# ────────────────────────────────────────────────────────────────
# 📌 reflexe.py — Commande interactive !reflexe
# Objectif : Tester les réflexes du joueur en cliquant à exactement 10 secondes
# Catégorie : Fun
# Accès : Public
# ────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ───────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import time
from utils.discord_utils import safe_send, safe_edit

# ───────────────────────────────────────────────────
# 🎮 Vue interactive pour la commande !reflexe
# ───────────────────────────────────────────────────
class ReflexeView(View):
    def __init__(self, start_time):
        super().__init__(timeout=20)
        self.start_time = start_time
        self.clicked = False
        self.add_item(ReflexeButton(self))

class ReflexeButton(Button):
    def __init__(self, parent_view):
        super().__init__(style=discord.ButtonStyle.success, label="Clique !", custom_id="reflexe_btn")
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.clicked:
            await interaction.response.send_message("Tu as déjà cliqué !", ephemeral=True)
            return

        self.parent_view.clicked = True
        elapsed = time.perf_counter() - self.parent_view.start_time
        ecart = abs(elapsed - 10)

        if elapsed < 10:
            message = f"Trop tôt ! Tu as cliqué à {elapsed:.2f}s."
        elif elapsed > 10.5:
            message = f"Trop tard ! Tu as cliqué à {elapsed:.2f}s."
        else:
            message = f"🎉 Parfait ! Tu as cliqué à {elapsed:.2f}s."

        await safe_edit(interaction.message, content=message, view=None)


# ───────────────────────────────────────────────────
# 🧠 Cog principal
# ───────────────────────────────────────────────────
class Reflexe(commands.Cog):
    """
    Commande !reflexe — Clique à exactement 10 secondes !
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="reflexe",
        help="Teste tes réflexes en cliquant à 10 secondes.",
        description="Clique sur le bouton le plus près possible de 10 secondes."
    )
    async def reflexe(self, ctx: commands.Context):
        """Lance le test de réflexe."""
        try:
            await safe_send(ctx.channel, f"🕐 Sois prêt... Clique à **10 secondes** !")
            await discord.utils.sleep_until(discord.utils.utcnow() + discord.utils.timedelta(seconds=1))
            start_time = time.perf_counter()
            view = ReflexeView(start_time)
            await safe_send(ctx.channel, "Appuie quand tu penses que 10 secondes sont passées :", view=view)
        except Exception as e:
            print(f"[ERREUR reflexe] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue pendant le test de réflexe.")

# ───────────────────────────────────────────────────
# 🔌 Setup du Cog
# ───────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Reflexe(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
