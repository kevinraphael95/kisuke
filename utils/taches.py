# ────────────────────────────────────────────────────────────────────────────────
# 📌 utils/taches.py — Mini-jeux (tâches) pour le bot
# Objectif : Fournir des mini-jeux interactifs réutilisables pour d’autres commandes
# Auteur : Toi
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
import random
import asyncio
import json
import os

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des personnages (pour bmoji)
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_emojis.json")

def load_characters():
    with open(DATA_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Fonctions des mini-jeux (tâches)
# Chaque fonction prend un `discord.Interaction` et retourne un booléen réussite.
# ────────────────────────────────────────────────────────────────────────────────

async def lancer_emoji(interaction: discord.Interaction) -> bool:
    pool = ["💀", "🌀", "🔥", "🌪️", "🌟", "🍥", "🍡", "🧊", "❄️", "💨"]
    sequence = random.sample(pool, 3)
    autres = [e for e in pool if e not in sequence]
    mix = sequence + random.sample(autres, 2)
    random.shuffle(mix)

    msg = await interaction.followup.send(
        f"🔁 Reproduis cette séquence : {' → '.join(sequence)}\nTu as 2 minutes !"
    )
    for e in mix:
        try: await msg.add_reaction(e)
        except: pass

    reponses = {}
    def check(r, u):
        if u.bot or r.message.id != msg.id:
            return False
        if u.id not in reponses:
            reponses[u.id] = []
        idx = len(reponses[u.id])
        if str(r.emoji) == sequence[idx]:
            reponses[u.id].append(str(r.emoji))
        return reponses[u.id] == sequence

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=120)
        await interaction.followup.send(f"✅ Séquence correcte {user.mention} !", ephemeral=True)
        return True
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Personne n'a réussi.", ephemeral=True)
        return False

async def lancer_reflexe(interaction: discord.Interaction) -> bool:
    compte = ["5️⃣", "4️⃣", "3️⃣", "2️⃣", "1️⃣"]
    msg = await interaction.followup.send("🕒 Clique dans l’ordre `5️⃣ 4️⃣ 3️⃣ 2️⃣ 1️⃣` !")
    for e in compte:
        await msg.add_reaction(e)

    reponses = {}
    def check(r, u):
        if u.bot or r.message.id != msg.id:
            return False
        if u.id not in reponses:
            reponses[u.id] = []
        idx = len(reponses[u.id])
        if str(r.emoji) == compte[idx]:
            reponses[u.id].append(str(r.emoji))
        return reponses[u.id] == compte

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=20)
        await interaction.followup.send(f"⚡ Réflexe parfait {user.mention} !", ephemeral=True)
        return True
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Aucun réflexe parfait.", ephemeral=True)
        return False

async def lancer_fleche(interaction: discord.Interaction) -> bool:
    fleches = ["⬅️", "⬆️", "⬇️", "➡️"]
    sequence = [random.choice(fleches) for _ in range(5)]
    tmp = await interaction.followup.send(f"🧭 Mémorise : `{' '.join(sequence)}` (5 s)")
    await asyncio.sleep(5)
    await tmp.delete()
    msg = await interaction.followup.send("🔁 Reproduis la séquence en cliquant :")

    for e in fleches:
        await msg.add_reaction(e)

    reponses = {}
    def check(r, u):
        if u.bot or r.message.id != msg.id:
            return False
        if u.id not in reponses:
            reponses[u.id] = []
        pos = len(reponses[u.id])
        if pos >= len(sequence): return False
        attendu = sequence[pos]
        if str(r.emoji) == attendu:
            reponses[u.id].append(str(r.emoji))
            asyncio.create_task(msg.remove_reaction(r.emoji, u))
            return len(reponses[u.id]) == len(sequence)
        else:
            reponses[u.id] = []
            return False

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=30)
        await interaction.followup.send(f"✅ Bien joué {user.mention} !", ephemeral=True)
        return True
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Personne n'a réussi.", ephemeral=True)
        return False

async def lancer_infusion(interaction: discord.Interaction) -> bool:
    await interaction.followup.send("🔵 Prépare-toi à synchroniser ton Reiatsu...")
    await asyncio.sleep(2)
    msg = await interaction.followup.send("🔵")
    for _ in range(3):
        await asyncio.sleep(0.6)
        await msg.edit(content="🔵🔵")
        await asyncio.sleep(0.6)
        await msg.edit(content="🔵🔵🔵")
    await asyncio.sleep(0.5)
    await msg.edit(content="🔴")
    await msg.add_reaction("⚡")
    start = discord.utils.utcnow()

    def check(r, u):
        if u.bot or r.message.id != msg.id or str(r.emoji) != "⚡":
            return False
        delta = (discord.utils.utcnow() - start).total_seconds()
        return 0.8 <= delta <= 1.2

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=2)
        await interaction.followup.send(f"✅ Synchronisation parfaite, {user.mention} !", ephemeral=True)
        return True
    except asyncio.TimeoutError:
        await interaction.followup.send("❌ Échec, Reiatsu instable.", ephemeral=True)
        return False

class EmojiBoutons(discord.ui.View):
    def __init__(self, vrai: bool):
        super().__init__(timeout=15)
        self.vrai = vrai
        self.repondu = False

    @discord.ui.button(label="✅ Oui", style=discord.ButtonStyle.success)
    async def oui(self, inter, btn):
        if self.repondu: return
        self.repondu = True
        await self.verifie(inter, True)

    @discord.ui.button(label="❌ Non", style=discord.ButtonStyle.danger)
    async def non(self, inter, btn):
        if self.repondu: return
        self.repondu = True
        await self.verifie(inter, False)

    async def verifie(self, inter, rep):
        if rep == self.vrai:
            await inter.response.send_message("✅ Bonne réponse !", ephemeral=True)
        else:
            await inter.response.send_message("❌ Mauvaise réponse.", ephemeral=True)
        self.stop()

async def lancer_emoji9(interaction: discord.Interaction) -> bool:
    groupes = [["🍎","🍅"],["☁️","🌥️"],["☘️","🍀"],["🌺","🌸"],
               ["👜","💼"],["🌹","🌷"],["🤞","✌️"],["✊","👊"],
               ["😕","😐"],["🌟","⭐"],["🦝","🐨"],["🔒","🔓"],
               ["🏅","🥇"],["🌧️","🌨️"],["🐆","🐅"],["🙈","🙊"],
               ["🐋","🐳"],["🐢","🐊"]]
    base, intrus = random.choice(groupes)
    has_intrus = random.choice([True, False])
    emojis = [base]*9
    if has_intrus:
        emojis[random.randint(0,8)] = intrus
    random.shuffle(emojis)
    ligne = "".join(emojis)

    embed = discord.Embed(
        title="🔎 Tous identiques ?",
        description=f"{ligne}\n✅ si oui, ❌ si non",
        color=discord.Color.orange()
    )
    view = EmojiBoutons(vrai=(not has_intrus))
    await interaction.followup.send(embed=embed, view=view)
    try:
        await interaction.client.wait_for("interaction", timeout=15)
        return True
    except asyncio.TimeoutError:
        return False

async def lancer_bmoji(interaction: discord.Interaction) -> bool:
    characters = load_characters()
    pers = random.choice(characters)
    nom = pers["nom"]
    emojis = random.sample(pers["emojis"], k=min(3, len(pers["emojis"])))
    autres = [c["nom"] for c in characters if c["nom"] != nom]
    distracteurs = random.sample(autres, 3)
    options = distracteurs + [nom]
    random.shuffle(options)
    lettres = ["🇦","🇧","🇨","🇩"]
    bonne = lettres[options.index(nom)]

    embed = discord.Embed(
        title="🔍 Devine le perso",
        description="Emoji➤Perso",
        color=0x1abc9c
    )
    embed.add_field(name="Emojis", value=" ".join(emojis), inline=False)
    embed.add_field(
        name="Choix",
        value="\n".join(f"{lettres[i]}: {options[i]}" for i in range(4)),
        inline=False
    )
    embed.set_footer(text="Réagis 🇦 🇧 🇨 ou 🇩")
    message = await interaction.followup.send(embed=embed)
    for e in lettres:
        await message.add_reaction(e)

    def check(r, u):
        return u == interaction.user and r.message.id == message.id and str(r.emoji) in lettres

    try:
        r, u = await interaction.client.wait_for("reaction_add", check=check, timeout=30)
        if str(r.emoji) == bonne:
            await interaction.followup.send(f"✅ Bravo {u.mention} !", ephemeral=True)
            return True
        else:
            await interaction.followup.send(f"❌ Mauvaise réponse.", ephemeral=True)
            return False
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Temps écoulé.", ephemeral=True)
        return False

# ────────────────────────────────────────────────────────────────────────────────
# 🔁 Fonction pour lancer 3 tâches aléatoires (réutilisable)
# ────────────────────────────────────────────────────────────────────────────────

TACHES = [
    lancer_emoji,
    lancer_reflexe,
    lancer_fleche,
    lancer_infusion,
    lancer_emoji9,
    lancer_bmoji,
]

async def lancer_3_taches(interaction: discord.Interaction) -> bool:
    """Lance 3 tâches aléatoires différentes, retourne True si toutes réussies."""
    choisies = random.sample(TACHES, 3)
    reussites = []
    for tache in choisies:
        res = await tache(interaction)
        reussites.append(res)
        if not res:
            break
    return all(reussites)
