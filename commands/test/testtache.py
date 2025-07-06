# ────────────────────────────────────────────────────────────────────────────────
# 📌 test_taches.py — Commande interactive !testtache
# Objectif : Tester toutes les tâches interactives du mode Hollow Among Us
# Catégorie : Bleach / Mini-jeux
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Select
import asyncio
import random

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Tâches disponibles
# ────────────────────────────────────────────────────────────────────────────────
TACHES = {
    "Quiz Bleach": "quiz",
    "Code": "code",
    "Séquence emoji": "emoji",
    "Réflexe rapide": "reflexe",
    "Séquence fléchée": "fleche",
    "Infusion de Reiatsu": "infusion",
    "Emoji suspects": "emoji9",
    "Bmoji": "bmoji"
    
}

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Mots possibles pour Code
# ────────────────────────────────────────────────────────────────────────────────
MOTS_CODE = [
    "hollow", "shinigami", "quincy", "zanpakuto", 
    "shikai", "bankai", "kido", "shunpo", 
    "karakura", "vizard", "capitaine", "reiatsu"
]

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu de sélection des tâches
# ────────────────────────────────────────────────────────────────────────────────
class TacheSelectView(View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.bot = bot
        self.add_item(TacheSelect(self))

class TacheSelect(Select):
    def __init__(self, parent_view: TacheSelectView):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=label, value=value) for label, value in TACHES.items()]
        super().__init__(placeholder="Choisis une tâche à tester", options=options)

    async def callback(self, interaction: discord.Interaction):
        task_type = self.values[0]
        await interaction.response.edit_message(content=f"🔧 Tâche sélectionnée : `{task_type}`", view=None)

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
# 🔹 Fonctions de tâches (mini-jeux)
# ────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────
# 🔎 Quizz naze a une seule question
# ────────────────────────────────────────────────────────────────────────────────

async def lancer_quiz(interaction):
    question = "Quel capitaine a pour zanpakutō Senbonzakura?"
    bonne_reponse = "Byakuya"

    await interaction.followup.send(f"❓ {question}\nRéponds avec `!rep <ta réponse>`.")

    def check(m):
        return m.channel == interaction.channel and m.content.startswith("!rep")

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=15)
        reponse = msg.content[5:].strip().lower()
        if reponse == bonne_reponse.lower():
            await interaction.followup.send(f"✅ Bonne réponse {msg.author.mention} !")
        else:
            await interaction.followup.send(f"❌ Mauvaise réponse {msg.author.mention} !")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Temps écoulé, personne n'a répondu.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔎 Mot code
# ────────────────────────────────────────────────────────────────────────────────

async def lancer_code(interaction):
    mot = random.choice(MOTS_CODE)
    lettres = list(mot)
    indices_manquants = random.sample(range(len(lettres)), k=min(3, len(mot)//2))
    mot_code = ''.join('_' if i in indices_manquants else c.upper() for i, c in enumerate(lettres))

    await interaction.followup.send(f"🔐 Trouve le mot : `{mot_code}` — Réponds avec `!rep <mot>`")

    def check(m):
        return m.channel == interaction.channel and m.content.startswith("!rep")

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=10)
        if msg.content[5:].strip().lower() == mot:
            await interaction.followup.send(f"✅ Bien joué {msg.author.mention}, c'était `{mot.upper()}` !")
        else:
            await interaction.followup.send(f"❌ Mauvais mot {msg.author.mention}.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Trop tard.")

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
        description="Appuie sur ✅ si **tous** les emojis sont identiques,\n❌ sinon.",
        color=discord.Color.orange()
    )

    await interaction.followup.send(embed=embed, view=EmojiBoutons(not y_a_intrus))
    await interaction.followup.send(ligne)


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────

async def lancer_bmoji(interaction):
    # Liste de personnages avec leur "trio d'emojis" et leur nom
    personnages = [
        {"emojis": "🦇🗡️🌑", "nom": "Ulquiorra"},
        {"emojis": "🐉🔥🗡️", "nom": "Ichigo"},
        {"emojis": "🐸🧙‍♂️🎩", "nom": "Yoruichi"},
        {"emojis": "🕊️⚔️✨", "nom": "Rukia"},
        {"emojis": "👺🍙⚡", "nom": "Renji"},
        {"emojis": "🐺❄️🔥", "nom": "Toshiro"},
        # Ajoute-en autant que tu veux
    ]

    # Choisir un personnage au hasard
    correct = random.choice(personnages)

    # Préparer 3 fausses réponses + la bonne
    noms_possibles = [p["nom"] for p in personnages if p != correct]
    fausses_reponses = random.sample(noms_possibles, k=3)
    options = fausses_reponses + [correct["nom"]]
    random.shuffle(options)

    # Lettres correspondantes aux réactions
    lettres = ['🇦', '🇧', '🇨', '🇩']

    # Construire le texte avec les propositions
    description = f"Devine le personnage représenté par ces emojis : {correct['emojis']}\n\n"
    for i, option in enumerate(options):
        description += f"{lettres[i]} - {option}\n"

    embed = discord.Embed(
        title="🧐 Quel est ce personnage ?",
        description=description,
        color=discord.Color.purple()
    )

    message = await interaction.followup.send(embed=embed)

    # Ajouter les réactions A, B, C, D
    for lettre in lettres:
        await message.add_reaction(lettre)

    def check(reaction, user):
        return (
            user != interaction.client.user and
            reaction.message.id == message.id and
            str(reaction.emoji) in lettres
        )

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=30)
        choix = lettres.index(str(reaction.emoji))
        reponse = options[choix]

        if reponse == correct["nom"]:
            await interaction.followup.send(f"✅ Bravo {user.mention} ! C’est bien **{correct['nom']}**.")
        else:
            await interaction.followup.send(f"❌ Désolé {user.mention}, c’était **{correct['nom']}**.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Temps écoulé, personne n'a répondu.")





        
# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class TestTache(commands.Cog):
    """
    Commande !testtache — Teste les différentes tâches du mode Hollow
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="testtache",
        help="Test des tâches interactives.",
        description="Testez les mini-jeux de tâches inspirées d'Among Us Hollow."
    )
    async def testtache(self, ctx: commands.Context):
        try:
            view = TacheSelectView(self.bot)
            await ctx.send("🧪 Choisis une tâche à tester :", view=view)
        except Exception as e:
            print(f"[ERREUR testtache] {e}")
            await ctx.send("❌ Erreur lors de l'affichage des tâches.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TestTache(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
