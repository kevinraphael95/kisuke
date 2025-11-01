# ────────────────────────────────────────────────────────────────────────────────
# 📌 quizzpays.py — Jeu /quizzpays et !quizzpays : Trouve le drapeau ou la capitale !
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
import aiohttp, random, asyncio
from utils.discord_utils import safe_send, safe_respond, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
async def get_random_countries(n=4):
    """Retourne n pays aléatoires depuis restcountries."""
    url = "https://restcountries.com/v3.1/all"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            data = await r.json()
    selected = random.sample(data, n)
    return [{
        "name": c["name"]["common"],
        "flag": c.get("flags", {}).get("png"),
        "capital": c.get("capital", ["?"])[0]
    } for c in selected if "flags" in c]

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 UI — Boutons du quizz
# ────────────────────────────────────────────────────────────────────────────────
class QuizButton(Button):
    def __init__(self, label, correct, parent_view):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.correct = correct
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.parent_view.player:
            await interaction.response.send_message("❌ Ce quizz ne t’est pas destiné !", ephemeral=True)
            return

        for child in self.parent_view.children:
            child.disabled = True

        if self.correct:
            self.style = discord.ButtonStyle.success
            await interaction.response.edit_message(content="✅ Bonne réponse !", view=self.parent_view)
        else:
            self.style = discord.ButtonStyle.danger
            await interaction.response.edit_message(content="❌ Mauvaise réponse !", view=self.parent_view)

        await asyncio.sleep(1.5)
        await self.parent_view.next_question(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue principale
# ────────────────────────────────────────────────────────────────────────────────
class QuizzPaysView(View):
    def __init__(self, player, countries, channel):
        super().__init__(timeout=60)
        self.player = player
        self.countries = countries
        self.channel = channel
        self.current = 0
        self.correct_country = None
        self.question_type = None

    async def start(self):
        await self.next_question()

    async def next_question(self, interaction=None):
        # Choisir un type de question (drapeau ou capitale)
        self.question_type = random.choice(["flag", "capital"])
        self.correct_country = random.choice(self.countries)

        for child in list(self.children):
            self.remove_item(child)

        if self.question_type == "flag":
            # Question : Quel est le drapeau de ce pays ?
            question = f"🌍 **Quel est le drapeau de {self.correct_country['name']} ?**"
            random.shuffle(self.countries)
            for c in self.countries:
                btn = QuizButton(" ", c["name"] == self.correct_country["name"], self)
                btn.emoji = None
                btn.style = discord.ButtonStyle.secondary
                btn.flag_url = c["flag"]
                self.add_item(btn)

            embed = discord.Embed(title=question, color=discord.Color.blurple())
            # afficher drapeaux via liens dans les boutons (Discord ne supporte pas images dans boutons)
            flags_text = "\n".join([f"{i+1}. [Voir le drapeau]({c['flag']})" for i, c in enumerate(self.countries)])
            embed.description = flags_text

        else:
            # Question : Quelle est la capitale de ce pays ?
            question = f"🏙️ **Quelle est la capitale de {self.correct_country['name']} ?**"
            capitals = [c["capital"] for c in self.countries]
            random.shuffle(capitals)
            for cap in capitals:
                self.add_item(QuizButton(cap, cap == self.correct_country["capital"], self))
            embed = discord.Embed(title=question, color=discord.Color.orange())

        # Envoyer ou mettre à jour
        if interaction:
            await safe_edit(interaction.message, embed=embed, view=self)
        else:
            await safe_send(self.channel, embed=embed, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class QuizzPays(commands.Cog):
    """
    Commande /quizzpays et !quizzpays — Trouve le drapeau ou la capitale d’un pays.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _start_quizz(self, channel, user):
        try:
            countries = await get_random_countries(4)
            view = QuizzPaysView(user, countries, channel)
            await view.start()
        except Exception as e:
            print(f"[ERREUR quizzpays] {e}")
            await safe_send(channel, "❌ Impossible de lancer le quizz. Réessaie plus tard.")

    # ──────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ──────────────────────────────────────────────────────────────
    @app_commands.command(
        name="quizzpays",
        description="Teste tes connaissances sur les drapeaux et capitales des pays !"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_quizzpays(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._start_quizz(interaction.channel, interaction.user)
        await interaction.delete_original_response()

    # ──────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ──────────────────────────────────────────────────────────────
    @commands.command(name="quizzpays", aliases=["qp"])
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_quizzpays(self, ctx: commands.Context):
        await self._start_quizz(ctx.channel, ctx.author)

# ──────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = QuizzPays(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
