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
        if task == "emoji":
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



# ────────────────────────────────────────────────────────────────────────────────
# 🔎 Séquence emojis
# ────────────────────────────────────────────────────────────────────────────────

async def lancer_emoji(interaction):
    pool = ["💀", "🌀", "🔥", "🌪️", "🌟", "🍥", "🍡", "🧊", "❄️", "💨"]
    sequence = random.sample(pool, 3)
    autres = [e for e in pool if e not in sequence]
    mix = sequence + random.sample(autres, 2)
    random.shuffle(mix)

    message = await interaction.followup.send(
        f"🔁 Reproduis cette séquence en cliquant les réactions **dans l'ordre** : {' → '.join(sequence)}\n"
        f"Tu as 2 minutes ! Le premier qui réussit gagne."
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
        await interaction.followup.send(f"✅ Séquence correcte {user.mention} !")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Personne n'a réussi.")

        

# ────────────────────────────────────────────────────────────────────────────────
# de 5 a 1
# ────────────────────────────────────────────────────────────────────────────────
async def lancer_reflexe(interaction):
    compte = ["5️⃣", "4️⃣", "3️⃣", "2️⃣", "1️⃣"]
    message = await interaction.followup.send("🕒 Clique les réactions `5️⃣ 4️⃣ 3️⃣ 2️⃣ 1️⃣` **dans l'ordre** le plus vite possible !")

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
        await interaction.followup.send(f"⚡ Réflexe parfait, {user.mention} !")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Aucun réflexe parfait enregistré.")



# ────────────────────────────────────────────────────────────────────────────────
# 🔎 Code avec les flècches
# ────────────────────────────────────────────────────────────────────────────────
async def lancer_fleche(interaction):
    fleches = ["⬅️", "⬆️", "⬇️", "➡️"]
    sequence = [random.choice(fleches) for _ in range(5)]

    # Afficher la séquence pendant 5 secondes
    affichage = await interaction.followup.send(
        f"🧭 Mémorise cette séquence de flèches :\n`{' '.join(sequence)}`\nTu as 5 secondes..."
    )
    await asyncio.sleep(5)
    await affichage.delete()

    # Message avec réactions
    message = await interaction.followup.send(
        "🔁 Reproduis la séquence **dans le bon ordre** en cliquant les flèches ci-dessous.\n"
        "Chaque clic correct supprime l'emoji correspondant.\nTu as 30 secondes !"
    )

    for emoji in fleches:
        await message.add_reaction(emoji)

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
            reponses[user.id] = []  # reset
            return False

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=30)
        await interaction.followup.send(f"✅ Séquence parfaite {user.mention} !")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Personne n'a réussi la séquence.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔎 Boule bleu devient rouge
# ────────────────────────────────────────────────────────────────────────────────

async def lancer_infusion(interaction):
    await interaction.followup.send("🔵 Prépare-toi à synchroniser ton Reiatsu...")

    await asyncio.sleep(2)

    # Étapes de remplissage du cercle
    message = await interaction.followup.send("🔵")
    for _ in range(3):
        await asyncio.sleep(0.6)
        await message.edit(content="🔵🔵")
        await asyncio.sleep(0.6)
        await message.edit(content="🔵🔵🔵")

    # Passage en rouge
    await asyncio.sleep(0.5)
    await message.edit(content="🔴")

    # Délai d’activation de la réaction
    await message.add_reaction("⚡")
    start_time = discord.utils.utcnow()

    def check(reaction, user):
        if user.bot:
            return False
        if reaction.message.id != message.id:
            return False
        if str(reaction.emoji) != "⚡":
            return False
        delta = (discord.utils.utcnow() - start_time).total_seconds()
        return 0.8 <= delta <= 1.2  # ✅ Fenêtre parfaite

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=2)
        await interaction.followup.send(f"✅ {user.mention}, Synchronisation parfaite ! Ton Reiatsu est stable.")
    except asyncio.TimeoutError:
        await interaction.followup.send("❌ Échec de l’infusion. Reiatsu instable.")


# ────────────────────────────────────────────────────────────────────────────────
# 🔎 9 Emojis – Trouve l’intrus
# ────────────────────────────────────────────────────────────────────────────────
class EmojiBoutons(discord.ui.View):
    def __init__(self, vrai_reponse):
        super().__init__(timeout=15)
        self.vrai_reponse = vrai_reponse
        self.repondu = False

    @discord.ui.button(label="✅ Oui", style=discord.ButtonStyle.success)
    async def bouton_vrai(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.repondu:
            return
        self.repondu = True
        await self.verifie(interaction, True)

    @discord.ui.button(label="❌ Non", style=discord.ButtonStyle.danger)
    async def bouton_faux(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.repondu:
            return
        self.repondu = True
        await self.verifie(interaction, False)

    async def verifie(self, interaction, reponse):
        if reponse == self.vrai_reponse:
            await interaction.response.send_message("✅ Bonne réponse !", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Mauvaise réponse !", ephemeral=True)
        self.stop()

async def lancer_emoji9(interaction):
    groupes = [
        ["🍎", "🍅"], ["☁️", "🌥️"], ["☘️", "🍀"], ["🌺", "🌸"], 
        ["👜", "💼"], ["🌹", "🌷"], ["🤞", "✌️"], ["✊", "👊"], 
        ["😕", "😐"], ["🌟", "⭐"], ["🦝", "🐨"], ["🔒", "🔓"], 
        ["🏅", "🥇"], ["🌧️", "🌨️"], ["🐆", "🐅"], ["🙈", "🙊"], 
        ["🐋", "🐳"], ["🐢", "🐊"]
    ]

    base, intrus = random.choice(groupes)
    y_a_intrus = random.choice([True, False])

    if y_a_intrus:
        emojis = [base] * 9
        emojis[random.randint(0, 8)] = intrus
        random.shuffle(emojis)
    else:
        emojis = [base] * 9

    ligne = "".join(emojis)

    embed = discord.Embed(
        title="🔎 Tous identiques ?",
        description=f"{ligne}\n\nAppuie sur ✅ si **tous** les emojis sont identiques,\n❌ sinon.",
        color=discord.Color.orange()
    )

    await interaction.followup.send(embed=embed, view=EmojiBoutons(not y_a_intrus))



# ────────────────────────────────────────────────────────────────────────────────
# 🔎 Bmoji — Devine le personnage à partir des emojis
# ────────────────────────────────────────────────────────────────────────────────
async def lancer_bmoji(interaction):
    characters = load_characters()
    personnage = random.choice(characters)
    nom_correct = personnage["nom"]

    # Sélectionner 3 emojis aléatoires parmi ceux du personnage (sans doublons)
    emojis = random.sample(personnage["emojis"], k=min(3, len(personnage["emojis"])))

    # Générer 3 autres noms de personnages différents
    autres = [c["nom"] for c in characters if c["nom"] != nom_correct]
    distracteurs = random.sample(autres, 3)

    # Mélanger la bonne réponse avec les distracteurs
    propositions = distracteurs + [nom_correct]
    random.shuffle(propositions)

    emoji_lettres = ["🇦", "🇧", "🇨", "🇩"]
    lettre_index = propositions.index(nom_correct)
    bonne_reaction = emoji_lettres[lettre_index]


    # Création de l'embed
    embed = Embed(
        title="🔍 Devine le personnage Bleach",
        description="Quel personnage Bleach est représenté par ces emojis ?",
        color=0x1abc9c  # couleur turquoise par exemple
    )

    # Ajouter un champ pour les emojis
    embed.add_field(
        name="Emojis",
        value=' '.join(emojis),
        inline=False
    )

    # Ajouter un champ pour les propositions
    propositions_text = "\n".join(f"{emoji_lettres[i]}: {propositions[i]}" for i in range(4))
    embed.add_field(
        name="Choisis ta réponse",
        value=propositions_text,
        inline=False
    )

    # Ajouter une note sur la réaction
    embed.set_footer(text="Réagis avec 🇦 🇧 🇨 ou 🇩 pour répondre.")

    # Envoyer l'embed
    message = await interaction.followup.send(embed=embed)

    # Ajout des réactions pour le choix
    for emoji in emoji_lettres:
        await message.add_reaction(emoji)

    def check(reaction, user):
        return (
            user == interaction.user
            and reaction.message.id == message.id
            and str(reaction.emoji) in emoji_lettres
        )

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=30)
        if str(reaction.emoji) == bonne_reaction:
            await interaction.followup.send(f"✅ Bravo {user.mention}, bonne réponse !")
        else:
            await interaction.followup.send(f"❌ Désolé {user.mention}, ce n'est pas la bonne réponse.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Temps écoulé, personne n'a répondu.")


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
