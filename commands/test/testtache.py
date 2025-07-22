# ────────────────────────────────────────────────────────────────────────────────
# 📌 test_taches.py — Commande interactive !testtache
# Objectif : Tester toutes les tâches interactives du mode Hollow Among Us (Bleach)
# Catégorie : Mini-jeux / Tests
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Select, Button
from discord import Embed
import asyncio
import random
import os
import json

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON — personnages Bleach avec emojis
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_emojis.json")

def load_characters():
    """Charge la liste des personnages avec leurs emojis depuis JSON."""
    with open(DATA_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 📋 Liste des tâches disponibles
# ────────────────────────────────────────────────────────────────────────────────
TACHES = {
    "Quiz Bleach": "quiz",
    "Mot code": "code",
    "Séquence emoji": "emoji",
    "Réflexe rapide": "reflexe",
    "Séquence fléchée": "fleche",
    "Infusion Reiatsu": "infusion",
    "Emoji suspects": "emoji9",
    "Bmoji (Devine le perso)": "bmoji"
}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI : Menu déroulant de sélection de tâche
# ────────────────────────────────────────────────────────────────────────────────
class TacheSelect(Select):
    def __init__(self, parent_view):
        options = [discord.SelectOption(label=label, value=val) for label, val in TACHES.items()]
        super().__init__(placeholder="Choisis une tâche à tester", options=options, min_values=1, max_values=1)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        task = self.values[0]
        # Désactive la sélection après choix
        self.parent_view.clear_items()
        await interaction.edit_original_response(content=f"🔧 Tâche sélectionnée : **{task}**", view=None)

        # Lancer la tâche correspondante
        if task == "quiz":
            await lancer_quiz(interaction)
        elif task == "code":
            await lancer_code(interaction)
        elif task == "emoji":
            await lancer_emoji(interaction)
        elif task == "reflexe":
            await lancer_reflexe(interaction)
        elif task == "fleche":
            await lancer_fleche(interaction)
        elif task == "infusion":
            await lancer_infusion(interaction)
        elif task == "emoji9":
            await lancer_emoji9(interaction)
        elif task == "bmoji":
            await lancer_bmoji(interaction)


class TacheSelectView(View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.bot = bot
        self.add_item(TacheSelect(self))

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Fonctions des mini-jeux (tâches)
# ────────────────────────────────────────────────────────────────────────────────

# -- Quiz simple --
async def lancer_quiz(interaction: discord.Interaction):
    question = "Quel capitaine a pour zanpakutō Senbonzakura ?"
    bonne_reponse = "byakuya"

    await interaction.followup.send(f"❓ {question}\nRéponds avec `!rep <ta réponse>`.")

    def check(m):
        return m.channel == interaction.channel and m.content.lower().startswith("!rep")

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=15)
        reponse = msg.content[5:].strip().lower()
        if reponse == bonne_reponse:
            await interaction.followup.send(f"✅ Bonne réponse {msg.author.mention} !")
        else:
            await interaction.followup.send(f"❌ Mauvaise réponse {msg.author.mention} ! La bonne réponse était `{bonne_reponse.title()}`.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Temps écoulé, personne n'a répondu.")

# -- Mot code --
MOTS_CODE = [
    "hollow", "shinigami", "quincy", "zanpakuto", 
    "shikai", "bankai", "kido", "shunpo", 
    "karakura", "vizard", "capitaine", "reiatsu"
]

async def lancer_code(interaction: discord.Interaction):
    mot = random.choice(MOTS_CODE)
    lettres = list(mot)
    nb_manquants = max(2, len(mot)//3)
    indices_manquants = random.sample(range(len(lettres)), k=nb_manquants)
    mot_code = ''.join('_' if i in indices_manquants else c.upper() for i, c in enumerate(lettres))

    await interaction.followup.send(f"🔐 Trouve le mot : `{mot_code}` — Réponds avec `!rep <mot>`")

    def check(m):
        return m.channel == interaction.channel and m.content.lower().startswith("!rep")

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=15)
        reponse = msg.content[5:].strip().lower()
        if reponse == mot:
            await interaction.followup.send(f"✅ Bravo {msg.author.mention}, c'était bien `{mot.upper()}` !")
        else:
            await interaction.followup.send(f"❌ Mauvaise réponse {msg.author.mention}, le mot était `{mot.upper()}`.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Trop tard pour répondre.")

# -- Séquence emoji --
async def lancer_emoji(interaction: discord.Interaction):
    pool = ["💀", "🌀", "🔥", "🌪️", "🌟", "🍥", "🍡", "🧊", "❄️", "💨"]
    sequence = random.sample(pool, 3)
    autres = [e for e in pool if e not in sequence]
    mix = sequence + random.sample(autres, 2)
    random.shuffle(mix)

    message = await interaction.followup.send(
        f"🔁 Reproduis cette séquence **dans l'ordre** en cliquant les réactions : {' → '.join(sequence)}\n"
        f"Tu as 2 minutes ! Premier qui réussit gagne."
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
        attendu_index = len(reponses[user.id])
        if attendu_index >= len(sequence):
            return False
        attendu = sequence[attendu_index]
        if str(reaction.emoji) == attendu:
            reponses[user.id].append(str(reaction.emoji))
            return reponses[user.id] == sequence
        else:
            reponses[user.id] = []
            return False

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=120)
        await interaction.followup.send(f"✅ Bravo {user.mention}, tu as reproduit la séquence !")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Personne n'a réussi la séquence.")

# -- Réflexe rapide --
async def lancer_reflexe(interaction: discord.Interaction):
    sequence = ["5️⃣", "4️⃣", "3️⃣", "2️⃣", "1️⃣"]
    message = await interaction.followup.send("🕒 Clique les réactions **dans l'ordre** : 5️⃣ 4️⃣ 3️⃣ 2️⃣ 1️⃣ — Le plus vite possible !")

    for emoji in sequence:
        await message.add_reaction(emoji)

    reponses = {}

    def check(reaction, user):
        if user.bot or reaction.message.id != message.id:
            return False
        if user.id not in reponses:
            reponses[user.id] = []
        attendu_index = len(reponses[user.id])
        if attendu_index >= len(sequence):
            return False
        if str(reaction.emoji) == sequence[attendu_index]:
            reponses[user.id].append(str(reaction.emoji))
            return reponses[user.id] == sequence
        else:
            reponses[user.id] = []
            return False

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=20)
        await interaction.followup.send(f"⚡ Réflexe parfait, bravo {user.mention} !")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Aucun réflexe parfait détecté.")

# -- Séquence flèches --
async def lancer_fleche(interaction: discord.Interaction):
    fleches = ["⬅️", "⬆️", "⬇️", "➡️"]
    sequence = [random.choice(fleches) for _ in range(5)]

    affichage = await interaction.followup.send(f"🧭 Mémorise cette séquence : `{' '.join(sequence)}` (5 secondes)")
    await asyncio.sleep(5)
    await affichage.delete()

    message = await interaction.followup.send(
        "🔁 Reproduis la séquence **dans l'ordre** en cliquant les flèches ci-dessous.\n"
        "Chaque clic correct supprimera l'emoji.\nTu as 30 secondes."
    )

    for f in fleches:
        await message.add_reaction(f)

    reponses = {}

    def check(reaction, user):
        if user.bot or reaction.message.id != message.id:
            return False
        if user.id not in reponses:
            reponses[user.id] = []
        pos = len(reponses[user.id])
        if pos >= len(sequence):
            return False
        attendu = sequence[pos]
        if str(reaction.emoji) == attendu:
            reponses[user.id].append(str(reaction.emoji))
            asyncio.create_task(message.remove_reaction(reaction.emoji, user))
            return len(reponses[user.id]) == len(sequence)
        else:
            reponses[user.id] = []
            return False

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=30)
        await interaction.followup.send(f"✅ Bien joué {user.mention}, séquence parfaite !")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Personne n'a réussi la séquence.")

# -- Infusion Reiatsu --
async def lancer_infusion(interaction: discord.Interaction):
    await interaction.followup.send("🔵 Prépare-toi à synchroniser ton Reiatsu...")

    message = await interaction.followup.send("🔵")

    for i in range(1, 4):
        await asyncio.sleep(0.6)
        await message.edit(content="🔵" * (i+1))

    await asyncio.sleep(0.5)
    await message.edit(content="🔴")

    await message.add_reaction("⚡")
    start = discord.utils.utcnow()

    def check(reaction, user):
        if user.bot or reaction.message.id != message.id:
            return False
        if str(reaction.emoji) != "⚡":
            return False
        elapsed = (discord.utils.utcnow() - start).total_seconds()
        return elapsed < 2.0

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=2)
        await interaction.followup.send(f"⚡ Synchronisation réussie, bravo {user.mention} !")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Trop lent, synchronisation ratée.")

# -- Emoji suspects (9 emojis) --
async def lancer_emoji9(interaction: discord.Interaction):
    characters = load_characters()
    suspects = random.sample(characters, 9)

    emojis = [perso["emoji"] for perso in suspects]
    noms = [perso["name"] for perso in suspects]

    message = await interaction.followup.send(
        "🕵️‍♂️ Trouve l'intrus parmi ces emojis :\n" +
        " ".join(emojis) +
        "\nRéponds avec `!rep <nom>`."
    )

    intrus = random.choice(noms)

    def check(m):
        return m.channel == interaction.channel and m.content.lower().startswith("!rep")

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=20)
        reponse = msg.content[5:].strip().lower()
        if reponse == intrus.lower():
            await interaction.followup.send(f"✅ Bravo {msg.author.mention}, c'était bien **{intrus}** l'intrus !")
        else:
            await interaction.followup.send(f"❌ Mauvaise réponse {msg.author.mention}, l'intrus était **{intrus}**.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Temps écoulé.")

# -- Bmoji (Devine le perso via emojis) --
async def lancer_bmoji(interaction: discord.Interaction):
    characters = load_characters()
    perso = random.choice(characters)
    emojis = perso.get("emojis", []) or [perso.get("emoji")]
    if not emojis:
        emojis = ["❓"]
    sequence = " ".join(emojis[:4])

    await interaction.followup.send(f"🧩 Devine ce personnage : {sequence}\nRéponds avec `!rep <nom>`.")

    def check(m):
        return m.channel == interaction.channel and m.content.lower().startswith("!rep")

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=20)
        reponse = msg.content[5:].strip().lower()
        if reponse == perso["name"].lower():
            await interaction.followup.send(f"✅ Bravo {msg.author.mention}, c'était bien **{perso['name']}** !")
        else:
            await interaction.followup.send(f"❌ Mauvaise réponse {msg.author.mention}, c'était **{perso['name']}**.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Trop tard pour répondre.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Commande principale !testtache
# ────────────────────────────────────────────────────────────────────────────────
class TestTache(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="testtache")
    async def test_tache(self, ctx):
        """Commande pour tester les mini-jeux interactifs."""
        view = TacheSelectView(self.bot)
        await ctx.send("🛠️ Choisis une tâche à tester dans le menu ci-dessous :", view=view)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TestTache(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
