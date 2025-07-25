# ────────────────────────────────────────────────────────────────────────────────
# 📌 topbleach.py — Commande interactive !topbleach
# Objectif : Classer 5 personnages de Bleach à l'aveugle dans un top 5
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
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des personnages Bleach
# ────────────────────────────────────────────────────────────────────────────────
BLEACH_DATA_PATH = os.path.join("data", "bleach_personnages.json")

def load_personnages_bleach():
    with open(BLEACH_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Vue interactive pour classer les personnages
# ────────────────────────────────────────────────────────────────────────────────
class ClassementBleachView(View):
    def __init__(self, bot, ctx, personnages):
        super().__init__(timeout=180)
        self.bot = bot
        self.ctx = ctx
        self.personnages = personnages
        self.index = 0
        self.classement = [None] * 5
        self.add_buttons()

    def add_buttons(self):
        self.clear_items()
        for i in range(5):
            label = f"{i+1}{['er', 'e', 'e', 'e', 'e'][i]} place"
            self.add_item(ClassementButton(label, i, self))

    async def prochain(self, interaction):
        self.index += 1
        if self.index >= len(self.personnages):
            await self.fin(interaction)
            return

        embed = discord.Embed(
            title=f"Personnage {self.index + 1} / 5",
            description=f"**{self.personnages[self.index]['nom']}**",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Classe ce personnage dans ton top 5.")
        self.add_buttons()
        await safe_edit(interaction.message, embed=embed, view=self)

    async def fin(self, interaction):
        embed = discord.Embed(
            title="🟢 Ton Top 5 Final des Personnages Bleach",
            color=discord.Color.green()
        )
        embed.description = "\n".join(
            f"**#{i + 1}** — {perso['nom']}" for i, perso in enumerate(self.classement) if perso
        )
        await safe_edit(interaction.message, content="Voici ton classement final :", embed=embed, view=None)
        await safe_send(self.ctx.channel, "🔍 Es-tu satisfait de ton top 5 ?", view=ValidationViewBleach(self.ctx.author))

# ────────────────────────────────────────────────────────────────────────────────
# 🔘 Boutons de classement
# ────────────────────────────────────────────────────────────────────────────────
class ClassementButton(Button):
    def __init__(self, label, position, view: ClassementBleachView):
        super().__init__(label=label, style=discord.ButtonStyle.blurple)
        self.position = position
        self.view_parent = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_parent.ctx.author:
            await safe_respond(interaction, "❌ Tu ne peux pas interagir avec ce jeu.", ephemeral=True)
            return

        if self.view_parent.classement[self.position] is not None:
            await safe_respond(interaction, "❌ Cette position est déjà prise.", ephemeral=True)
            return

        self.view_parent.classement[self.position] = self.view_parent.personnages[self.view_parent.index]
        await self.view_parent.prochain(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# ✅ Vue de validation finale
# ────────────────────────────────────────────────────────────────────────────────
class ValidationViewBleach(View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author
        self.add_item(Button(label="✅ Oui", style=discord.ButtonStyle.success, custom_id="oui"))
        self.add_item(Button(label="❌ Non", style=discord.ButtonStyle.danger, custom_id="non"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user == self.author

    @discord.ui.button(label="✅ Oui", style=discord.ButtonStyle.success)
    async def valider(self, interaction: discord.Interaction, button: discord.ui.Button):
        await safe_respond(interaction, "Merci pour ta participation !")

    @discord.ui.button(label="❌ Non", style=discord.ButtonStyle.danger)
    async def refuser(self, interaction: discord.Interaction, button: discord.ui.Button):
        await safe_respond(interaction, "D'accord, tu peux retenter la commande quand tu veux.")

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class TopBleach(commands.Cog):
    """Commande !topbleach — Classement interactif de personnages Bleach"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="topbleach",
        help="Classe 5 personnages de Bleach à l'aveugle.",
        description="Le bot te montre 5 persos de Bleach un à un, à classer dans ton top 5."
    )
    async def topbleach(self, ctx: commands.Context):
        try:
            persos = load_personnages_bleach()
            if not persos or len(persos) < 5:
                await safe_send(ctx.channel, "❌ Pas assez de personnages pour lancer le jeu.")
                return

            # Filtrage des doublons par nom
            unique_persos = {p['nom']: p for p in persos}.values()
            if len(unique_persos) < 5:
                await safe_send(ctx.channel, "❌ Pas assez de personnages uniques.")
                return

            selection = random.sample(list(unique_persos), 5)
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
