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
    """Retourne n pays aléatoires valides depuis restcountries."""
    url = "https://restcountries.com/v3.1/all?fields=name,flags,capital,cca2,region,currencies"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=10) as r:
            if r.status != 200:
                raise RuntimeError(f"Erreur API : {r.status}")
            data = await r.json()

    # filtrer les pays valides
    valid = [c for c in data if c.get("flags") and c.get("capital") and c.get("cca2")]
    if len(valid) < n:
        raise RuntimeError("Pas assez de pays valides récupérés.")
    return random.sample(valid, n)

def country_code_to_emoji(code: str) -> str:
    """Convertit un code pays (ISO 3166-1 alpha-2) en emoji drapeau."""
    return "".join(chr(ord(c) + 127397) for c in code.upper())

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
            self.parent_view.score += 1
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
    def __init__(self, player, countries, channel, max_questions=10):
        super().__init__(timeout=90)
        self.player = player
        self.countries = countries
        self.channel = channel
        self.max_questions = max_questions
        self.current = 0
        self.score = 0
        self.correct_country = None
        self.question_type = None

    async def start(self):
        await self.next_question()

    async def next_question(self, interaction=None):
        # Vérifier la fin du quizz
        if self.current >= self.max_questions:
            await self.end_quiz(interaction)
            return

        self.current += 1
        self.question_type = random.choice(["flag", "capital", "continent", "currency"])
        self.correct_country = random.choice(self.countries)

        for child in list(self.children):
            self.remove_item(child)

        if self.question_type == "flag":
            question = f"🌍 **({self.current}/{self.max_questions}) Quel est le drapeau de {self.correct_country['name']['common']} ?**"
            for c in self.countries:
                emoji = country_code_to_emoji(c['cca2'])
                btn = QuizButton(emoji, c["name"]["common"] == self.correct_country["name"]["common"], self)
                self.add_item(btn)

            embed = discord.Embed(title=question, color=discord.Color.blurple())
            embed.description = "Clique sur le bon emoji du drapeau."

        elif self.question_type == "capital":
            question = f"🏙️ **({self.current}/{self.max_questions}) Quelle est la capitale de {self.correct_country['name']['common']} ?**"
            capitals = [c["capital"][0] for c in self.countries]
            random.shuffle(capitals)
            for cap in capitals:
                self.add_item(QuizButton(cap, cap == self.correct_country["capital"][0], self))
            embed = discord.Embed(title=question, color=discord.Color.orange())

        elif self.question_type == "continent":
            question = f"🌐 **({self.current}/{self.max_questions}) Quel est le continent de {self.correct_country['name']['common']} ?**"
            continents = [c.get("region", "Inconnu") for c in self.countries]
            random.shuffle(continents)
            for cont in continents:
                self.add_item(QuizButton(cont, cont == self.correct_country.get("region", "Inconnu"), self))
            embed = discord.Embed(title=question, color=discord.Color.purple())

        elif self.question_type == "currency":
            question = f"💰 **({self.current}/{self.max_questions}) Quelle est la monnaie de {self.correct_country['name']['common']} ?**"
            currencies = [list(c.get("currencies", {"?"}).keys())[0] for c in self.countries]
            random.shuffle(currencies)
            for cur in currencies:
                self.add_item(QuizButton(cur, cur == list(self.correct_country.get("currencies", {"?"}).keys())[0], self))
            embed = discord.Embed(title=question, color=discord.Color.gold())

        if interaction:
            await safe_edit(interaction.message, embed=embed, view=self)
        else:
            await safe_send(self.channel, embed=embed, view=self)

    async def end_quiz(self, interaction=None):
        embed = discord.Embed(
            title="🏁 Fin du Quizz !",
            description=f"Tu as obtenu **{self.score}/{self.max_questions}** bonnes réponses 🎯",
            color=discord.Color.green()
        )
        for child in list(self.children):
            self.remove_item(child)

        if interaction:
            await safe_edit(interaction.message, content=None, embed=embed, view=None)
        else:
            await safe_send(self.channel, embed=embed)

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
            view = QuizzPaysView(user, countries, channel, max_questions=10)
            await view.start()
        except Exception as e:
            print(f"[ERREUR quizzpays] {e}")
            await safe_send(channel, "❌ Impossible de lancer le quizz. Réessaie plus tard.")

    # ──────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ──────────────────────────────────────────────────────────────
    @app_commands.command(
        name="quizzpays",
        description="Teste tes connaissances sur les drapeaux, capitales, continents et monnaies des pays !"
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
