# ────────────────────────────────────────────────────────────────────────────────
# 📌 test_taches.py — Commande interactive !testtache
# Objectif : Tester différentes tâches mini-jeux Hollow Among Us
# Catégorie : Bleach
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Select
import json
import os
import random
import asyncio
from utils.discord_utils import safe_send, safe_edit, safe_respond  # ✅ Utilisation des safe_

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON — personnages Bleach avec emojis
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_emojis.json")

def load_characters():
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu principal : catégories de tâches
# ────────────────────────────────────────────────────────────────────────────────
CATEGORIES = {
    "Mini-jeux classiques": {
        "Quiz Bleach": "quiz",
        "Code": "code",
        "Séquence emoji": "emoji",
        "Réflexe rapide": "reflexe",
        "Séquence fléchée": "fleche",
    },
    "Tâches spéciales": {
        "Infusion de Reiatsu": "infusion",
        "Emoji suspects": "emoji9",
        "Bmoji": "bmoji"
    }
}

class CategorySelectView(View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.bot = bot
        self.add_item(CategorySelect(self))

class CategorySelect(Select):
    def __init__(self, parent_view: CategorySelectView):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=cat, value=cat) for cat in CATEGORIES.keys()]
        super().__init__(placeholder="Sélectionne une catégorie de tâches", options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        new_view = TaskSelectView(self.parent_view.bot, category)
        await safe_edit(
            interaction.message,
            content=f"Catégorie sélectionnée : **{category}**\nChoisis une tâche à tester :",
            embed=None,
            view=new_view
        )

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu secondaire : choix de la tâche dans la catégorie
# ────────────────────────────────────────────────────────────────────────────────
class TaskSelectView(View):
    def __init__(self, bot, category):
        super().__init__(timeout=120)
        self.bot = bot
        self.category = category
        self.add_item(TaskSelect(self))

class TaskSelect(Select):
    def __init__(self, parent_view: TaskSelectView):
        self.parent_view = parent_view
        tasks = CATEGORIES[self.parent_view.category]
        options = [discord.SelectOption(label=label, value=value) for label, value in tasks.items()]
        super().__init__(placeholder="Sélectionne une tâche", options=options)

    async def callback(self, interaction: discord.Interaction):
        task_type = self.values[0]

        await safe_edit(
            interaction.message,
            content=f"Tâche choisie : **{task_type}**\nLancement du mini-jeu...",
            embed=None,
            view=None
        )

        # Lancement de la tâche correspondante
        if task_type == "quiz":
            await lancer_quiz(interaction)
        elif task_type == "code":
            await lancer_code(interaction)
        elif task_type == "emoji":
            await lancer_emoji(interaction)
        elif task_type == "reflexe":
            await lancer_reflexe(interaction)
        elif task_type == "fleche":
            await lancer_fleche(interaction)
        elif task_type == "infusion":
            await lancer_infusion(interaction)
        elif task_type == "emoji9":
            await lancer_emoji9(interaction)
        elif task_type == "bmoji":
            await lancer_bmoji(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Mini-jeux — Fonctions de chaque tâche
# ────────────────────────────────────────────────────────────────────────────────

MOTS_CODE = [
    "hollow", "shinigami", "quincy", "zanpakuto",
    "shikai", "bankai", "kido", "shunpo",
    "karakura", "vizard", "capitaine", "reiatsu"
]

async def lancer_quiz(interaction):
    question = "Quel capitaine a pour zanpakutō Senbonzakura?"
    bonne_reponse = "byakuya"

    await safe_send(interaction.channel, f"❓ {question}\nRéponds avec `!rep <ta réponse>`.")

    def check(m):
        return m.channel == interaction.channel and m.content.startswith("!rep")

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=15)
        reponse = msg.content[5:].strip().lower()
        if reponse == bonne_reponse:
            await safe_send(interaction.channel, f"✅ Bonne réponse {msg.author.mention} !")
        else:
            await safe_send(interaction.channel, f"❌ Mauvaise réponse {msg.author.mention} !")
    except asyncio.TimeoutError:
        await safe_send(interaction.channel, "⌛ Temps écoulé, personne n'a répondu.")

async def lancer_code(interaction):
    mot = random.choice(MOTS_CODE)
    lettres = list(mot)
    indices_manquants = random.sample(range(len(lettres)), k=min(3, len(mot)//2))
    mot_code = ''.join('_' if i in indices_manquants else c.upper() for i, c in enumerate(lettres))

    await safe_send(interaction.channel, f"🔐 Trouve le mot : `{mot_code}` — Réponds avec `!rep <mot>`")

    def check(m):
        return m.channel == interaction.channel and m.content.startswith("!rep")

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=10)
        if msg.content[5:].strip().lower() == mot:
            await safe_send(interaction.channel, f"✅ Bien joué {msg.author.mention}, c'était `{mot.upper()}` !")
        else:
            await safe_send(interaction.channel, f"❌ Mauvais mot {msg.author.mention}.")
    except asyncio.TimeoutError:
        await safe_send(interaction.channel, "⌛ Trop tard.")

async def lancer_emoji(interaction):
    pool = ["💀", "🌀", "🔥", "🌪️", "🌟", "🍥", "🍡", "🧊", "❄️", "💨"]
    sequence = random.sample(pool, 3)
    autres = [e for e in pool if e not in sequence]
    mix = sequence + random.sample(autres, 2)
    random.shuffle(mix)

    message = await safe_send(
        interaction.channel,
        f"🔁 Reproduis cette séquence en cliquant les réactions **dans l'ordre** : {' → '.join(sequence)}\n"
        "Tu as 2 minutes ! Le premier qui réussit gagne."
    )

    for emoji in mix:
        try:
            await message.add_reaction(emoji)
        except:
            pass

    reponses = {}

    def check(reaction, user):
        if user.bot or reaction.message.id != message.id:
            return False

        if user.id not in reponses:
            reponses[user.id] = []

        if str(reaction.emoji) == sequence[len(reponses[user.id])]:
            reponses[user.id].append(str(reaction.emoji))

        return reponses[user.id] == sequence

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=120)
        await safe_send(interaction.channel, f"✅ Séquence correcte {user.mention} !")
    except asyncio.TimeoutError:
        await safe_send(interaction.channel, "⌛ Personne n'a réussi.")

async def lancer_reflexe(interaction):
    compte = ["5️⃣", "4️⃣", "3️⃣", "2️⃣", "1️⃣"]
    message = await safe_send(interaction.channel, "🕒 Clique les réactions `5️⃣ 4️⃣ 3️⃣ 2️⃣ 1️⃣` **dans l'ordre** le plus vite possible !")

    for emoji in compte:
        await message.add_reaction(emoji)

    reponses = {}

    def check(reaction, user):
        if user.bot or reaction.message.id != message.id:
            return False

        if user.id not in reponses:
            reponses[user.id] = []

        if str(reaction.emoji) == compte[len(reponses[user.id])]:
            reponses[user.id].append(str(reaction.emoji))

        return reponses[user.id] == compte

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=20)
        await safe_send(interaction.channel, f"⚡ Réflexe parfait, {user.mention} !")
    except asyncio.TimeoutError:
        await safe_send(interaction.channel, "⌛ Aucun réflexe parfait enregistré.")

async def lancer_fleche(interaction):
    fleches = ["⬅️", "⬆️", "⬇️", "➡️"]
    sequence = [random.choice(fleches) for _ in range(5)]

    affichage = await safe_send(
        interaction.channel,
        f"🧭 Mémorise cette séquence de flèches :\n`{' '.join(sequence)}`\nTu as 5 secondes..."
    )
    await asyncio.sleep(5)
    await affichage.delete()

    message = await safe_send(
        interaction.channel,
        "Maintenant, reproduis la séquence en cliquant les réactions **dans l'ordre**."
    )
    for emoji in fleches:
        await message.add_reaction(emoji)

    reponses = {}

    def check(reaction, user):
        if user.bot or reaction.message.id != message.id:
            return False
        if user.id not in reponses:
            reponses[user.id] = []
        if str(reaction.emoji) == sequence[len(reponses[user.id])]:
            reponses[user.id].append(str(reaction.emoji))
        return reponses[user.id] == sequence

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=30)
        await safe_send(interaction.channel, f"✅ Bravo {user.mention}, tu as réussi !")
    except asyncio.TimeoutError:
        await safe_send(interaction.channel, "⌛ Temps écoulé, personne n'a réussi.")

async def lancer_infusion(interaction):
    await safe_send(interaction.channel, "⚡ Cette tâche est en cours de développement...")

async def lancer_emoji9(interaction):
    await safe_send(interaction.channel, "⚡ Cette tâche est en cours de développement...")

async def lancer_bmoji(interaction):
    await safe_send(interaction.channel, "⚡ Cette tâche est en cours de développement...")

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class TestTache(commands.Cog):
    """
    Commande !testtache — Tester différentes tâches mini-jeux Hollow Among Us
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="testtache",
        help="Tester une tâche interactive.",
        description="Lance un menu pour sélectionner et tester différentes tâches mini-jeux."
    )
    async def testtache(self, ctx: commands.Context):
        """Commande principale avec menu interactif pour tester une tâche."""
        try:
            view = CategorySelectView(self.bot)
            await safe_send(ctx.channel, "Choisis une catégorie de tâches :", view=view)
        except Exception as e:
            print(f"[ERREUR testtache] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors de l'initialisation.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TestTache(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
