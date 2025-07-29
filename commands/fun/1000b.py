# ────────────────────────────────────────────────────────────────────────────────
# 🏁 mille_bornes.py — Commande interactive !1000bornes
# Objectif : Mini-jeu 1000 Bornes simplifié pour 2 joueurs (toi vs bot)
# Catégorie : Autre
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import random
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Constantes du jeu
# ────────────────────────────────────────────────────────────────────────────────
MAX_DISTANCE = 1000
BOUTONS_JEU = ["🚗 Avancer", "🛑 Feu Rouge", "🧰 Réparer", "🛡️ Parade"]

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 UI — Vue principale du jeu 1000 Bornes
# ────────────────────────────────────────────────────────────────────────────────
class MilleBornesView(View):
    def __init__(self, ctx):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.joueur_km = 0
        self.bot_km = 0
        self.feu_rouge = False
        self.add_item(JouerBouton(self))

    async def jouer_tour_bot(self):
        if self.bot_km >= MAX_DISTANCE:
            return
        action = random.choice(["avancer", "feu_rouge", "parade"])
        if action == "avancer":
            self.bot_km += random.choice([25, 50, 75, 100])
        elif action == "feu_rouge":
            self.feu_rouge = True
        elif action == "parade":
            self.feu_rouge = False

    async def update_message(self, interaction):
        desc = f"**{self.ctx.author.display_name}** : {self.joueur_km} km\n**Bot** : {self.bot_km} km"
        if self.feu_rouge:
            desc += "\n🚨 Feu rouge actif ! Clique sur 🛡️ pour repartir."

        embed = discord.Embed(title="🏎️ 1000 Bornes — Mini-jeu", description=desc, color=0x2ecc71)
        embed.set_footer(text="Le premier à 1000 km gagne !")
        await safe_edit(interaction.message, embed=embed, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 👥 Bouton "Jouer" (simule une pioche + action)
# ────────────────────────────────────────────────────────────────────────────────
class JouerBouton(Button):
    def __init__(self, view: MilleBornesView):
        super().__init__(label="Jouer", style=discord.ButtonStyle.primary, emoji="🎲")
        self.view_ref = view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view_ref.ctx.author:
            return await interaction.response.send_message("⛔ Ce jeu ne t'appartient pas.", ephemeral=True)

        if self.view_ref.joueur_km >= MAX_DISTANCE:
            return await interaction.response.send_message("✅ Tu as déjà gagné !", ephemeral=True)

        carte = random.choice(["avancer", "feu_rouge", "reparer", "parade"])

        if carte == "avancer":
            if self.view_ref.feu_rouge:
                await interaction.response.send_message("🚫 Tu es à l'arrêt. Clique sur 🛡️ pour repartir.", ephemeral=True)
                return
            self.view_ref.joueur_km += random.choice([25, 50, 75, 100])
        elif carte == "feu_rouge":
            self.view_ref.feu_rouge = True
        elif carte == "reparer":
            self.view_ref.feu_rouge = False
        elif carte == "parade":
            self.view_ref.feu_rouge = False

        await self.view_ref.jouer_tour_bot()
        await self.view_ref.update_message(interaction)
        await interaction.response.defer()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class MilleBornes(commands.Cog):
    """
    Commande !1000bornes — Mini-jeu de course simplifié
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="1000bornes", aliases=["1000b", "1000"], help="Joue au 1000 Bornes contre le bot.", description="Mini-jeu de course jusqu'à 1000 km.")
    async def mille_bornes(self, ctx: commands.Context):
        try:
            view = MilleBornesView(ctx)
            embed = discord.Embed(
                title="🏎️ 1000 Bornes — Mini-jeu",
                description="**Objectif** : Atteins 1000 km avant le bot !\nClique sur 🎲 pour jouer.",
                color=0x2ecc71
            )
            await safe_send(ctx.channel, embed=embed, view=view)
        except Exception as e:
            print(f"[ERREUR 1000bornes] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue pendant la partie.")


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MilleBornes(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Autre" 
    await bot.add_cog(cog)
