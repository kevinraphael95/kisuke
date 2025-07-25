# ────────────────────────────────────────────────────────────────────────────────
# 📌 topbleach.py — Commande interactive !topbleach
# Objectif : Classer 5 personnages de Bleach dans un top 5 à l’aveugle
# Catégorie : Autre
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import random
import os
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des personnages de Bleach
# ────────────────────────────────────────────────────────────────────────────────
BLEACH_JSON_PATH = os.path.join("data", "bleach_personnages.json")

def load_personnages_bleach():
    with open(BLEACH_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 UI — Vue principale pour classer les personnages
# ────────────────────────────────────────────────────────────────────────────────
class ClassementBleachView(View):
    def __init__(self, bot, ctx, persos, index=0, classement=None):
        super().__init__(timeout=150)
        self.bot = bot
        self.ctx = ctx
        self.persos = persos
        self.index = index
        self.classement = classement or [None] * 5
        for i in range(5):
            if self.classement[i] is None:
                self.add_item(PositionButtonBleach(self, i))

    async def update_message(self, interaction):
        perso = self.persos[self.index]
        embed = discord.Embed(
            title=f"Personnage {self.index + 1} / 5",
            description=f"**{perso['nom']}**",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Choisis sa position dans ton top 5")
        await safe_edit(interaction.message, embed=embed, view=self)

    async def assign_position(self, interaction, pos):
        if self.classement[pos] is not None:
            await interaction.response.send_message("❌ Cette position est déjà prise.", ephemeral=True)
            return
        self.classement[pos] = self.persos[self.index]
        self.index += 1
        if self.index == len(self.persos):
            await self.fin(interaction)
            self.stop()
        else:
            self.clear_items()
            for i in range(5):
                if self.classement[i] is None:
                    self.add_item(PositionButtonBleach(self, i))
            await self.update_message(interaction)

    async def fin(self, interaction):
        embed = discord.Embed(
            title="🟢 Ton Top 5 Final des Personnages Bleach",
            color=discord.Color.green()
        )
        # Construction du texte avec un seul \n entre chaque entrée, sans espaces inutiles
        lines = []
        for i, perso in enumerate(self.classement):
            if perso:
                # Pas d'espaces avant/après, juste ligne propre
                lines.append(f"**#{i + 1} — {perso['nom']}**")
        embed.description = "\n".join(lines)

        await safe_edit(interaction.message, content="Voici ton classement final :", embed=embed, view=None)
        await safe_send(self.ctx.channel, "🔍 Es-tu satisfait de ton top 5 ?", view=ValidationViewBleach(self.ctx.author))


# ────────────────────────────────────────────────────────────────────────────────
# 🔘 UI — Boutons de position
# ────────────────────────────────────────────────────────────────────────────────
class PositionButtonBleach(Button):
    def __init__(self, parent_view: ClassementBleachView, position: int):
        super().__init__(label=f"#{position + 1}", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view
        self.position = position

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent_view.ctx.author:
            await interaction.response.send_message("⛔ Ce n'est pas à toi de jouer !", ephemeral=True)
            return
        await interaction.response.defer()
        await self.parent_view.assign_position(interaction, self.position)

# ────────────────────────────────────────────────────────────────────────────────
# ✅ UI — Validation finale
# ────────────────────────────────────────────────────────────────────────────────
class ValidationViewBleach(View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

    @discord.ui.button(label="👍 Oui", style=discord.ButtonStyle.success)
    async def yes(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Ce n’est pas ton top !", ephemeral=True)
            return
        await interaction.response.edit_message(content="🟩 Parfait, content que ça te plaise !", view=None)

    @discord.ui.button(label="👎 Non", style=discord.ButtonStyle.danger)
    async def no(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Ce n’est pas ton top !", ephemeral=True)
            return
        await interaction.response.edit_message(content="🔁 Peut-être que tu auras plus de chance la prochaine fois !", view=None)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class TopBleach(commands.Cog):
    """
    Commande !topbleach — Classe 5 personnages de Bleach dans un top 5
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="topperso", aliases=["topp"], 
        help="Classe 5 personnages de Bleach à l'aveugle.",
        description="Le bot te montre 5 persos de Bleach un à un, à classer dans ton top 5."
    )
    async def topbleach(self, ctx: commands.Context):
        """Commande principale de classement"""
        try:
            persos = load_personnages_bleach()
            if not persos or len(persos) < 5:
                await safe_send(ctx.channel, "❌ Pas assez de personnages pour lancer le jeu.")
                return
            selection = random.sample(persos, 5)
            view = ClassementBleachView(self.bot, ctx, selection)
            embed = discord.Embed(
                title="Personnage 1 / 5",
                description=f"**{selection[0]['nom']}**",
                color=discord.Color.orange()
            )
            embed.set_footer(text="Classe ce personnage dans ton top 5.")
            await safe_send(ctx.channel, embed=embed, view=view)
        except Exception as e:
            print(f"[ERREUR topbleach] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue pendant le jeu.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TopBleach(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
          
