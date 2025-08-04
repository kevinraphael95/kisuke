# ────────────────────────────────────────────────────────────────────────────────
# 📌 utils/taches.py — Mini-jeux (tâches) pour le bot
# Objectif : Mini-jeux interactifs affichés dynamiquement dans un embed unique
# ────────────────────────────────────────────────────────────────────────────────

import discord
import random
import asyncio
import json
import os

DATA_JSON_PATH = os.path.join("data", "bleach_emojis.json")

def load_characters():
    """Charge les personnages depuis le fichier JSON."""
    with open(DATA_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Fonctions des mini-jeux — version embed dynamique
# Chaque fonction prend :
# - interaction : discord.Interaction
# - embed : discord.Embed (à modifier)
# - update_embed : fonction async pour éditer l’embed dans le message
# - num : numéro de l’épreuve (affiché dans l’embed)
# Retourne True si réussite, False sinon.
# ────────────────────────────────────────────────────────────────────────────────

async def lancer_emoji(interaction, embed, update_embed, num):
    pool = ["💀", "🌀", "🔥", "🌪️", "🌟", "🍥", "🍡", "🧊", "❄️", "💨"]
    sequence = random.sample(pool, 3)
    autres = [e for e in pool if e not in sequence]
    mix = sequence + random.sample(autres, 2)
    random.shuffle(mix)

    msg = await interaction.channel.send(f"🔁 Reproduis cette séquence : {' → '.join(sequence)} (2 min)")
    for e in mix:
        try:
            await msg.add_reaction(e)
        except Exception:
            pass

    reponses = []

    def check(r, u):
        if u.bot or r.message.id != msg.id or u != interaction.user:
            return False
        if len(reponses) >= len(sequence):
            return False
        if str(r.emoji) == sequence[len(reponses)]:
            reponses.append(str(r.emoji))
            return True
        return False

    try:
        await interaction.client.wait_for("reaction_add", check=check, timeout=120)
        if reponses == sequence:
            embed.add_field(name=f"Épreuve {num}", value="✅ Séquence réussie", inline=False)
            await update_embed(embed)
            return True
        else:
            raise asyncio.TimeoutError()
    except asyncio.TimeoutError:
        embed.add_field(name=f"Épreuve {num}", value="❌ Échec de la séquence", inline=False)
        await update_embed(embed)
        return False

async def lancer_reflexe(interaction, embed, update_embed, num):
    compte = ["5️⃣", "4️⃣", "3️⃣", "2️⃣", "1️⃣"]
    msg = await interaction.channel.send("🕒 Clique dans l’ordre : `5️⃣ 4️⃣ 3️⃣ 2️⃣ 1️⃣`")
    for e in compte:
        await msg.add_reaction(e)

    reponses = []

    def check(r, u):
        if u.bot or r.message.id != msg.id or u != interaction.user:
            return False
        if len(reponses) >= len(compte):
            return False
        if str(r.emoji) == compte[len(reponses)]:
            reponses.append(str(r.emoji))
            return True
        return False

    try:
        await interaction.client.wait_for("reaction_add", check=check, timeout=20)
        if reponses == compte:
            embed.add_field(name=f"Épreuve {num}", value="⚡ Réflexe réussi", inline=False)
            await update_embed(embed)
            return True
        else:
            raise asyncio.TimeoutError()
    except asyncio.TimeoutError:
        embed.add_field(name=f"Épreuve {num}", value="❌ Échec du réflexe", inline=False)
        await update_embed(embed)
        return False

async def lancer_fleche(interaction, embed, update_embed, num):
    fleches = ["⬅️", "⬆️", "⬇️", "➡️"]
    sequence = [random.choice(fleches) for _ in range(5)]
    tmp = await interaction.channel.send(f"🧭 Mémorise : `{' '.join(sequence)}` (5 s)")
    await asyncio.sleep(5)
    await tmp.delete()
    msg = await interaction.channel.send("🔁 Reproduis la séquence :")
    for e in fleches:
        await msg.add_reaction(e)

    reponses = []

    def check(r, u):
        if u.bot or r.message.id != msg.id or u != interaction.user:
            return False
        if len(reponses) >= len(sequence):
            return False
        if str(r.emoji) == sequence[len(reponses)]:
            reponses.append(str(r.emoji))
            return True
        # mauvaise réaction réinitialise les réponses
        reponses.clear()
        return False

    try:
        await interaction.client.wait_for("reaction_add", check=check, timeout=30)
        if reponses == sequence:
            embed.add_field(name=f"Épreuve {num}", value="✅ Séquence fléchée réussie", inline=False)
            await update_embed(embed)
            return True
        else:
            raise asyncio.TimeoutError()
    except asyncio.TimeoutError:
        embed.add_field(name=f"Épreuve {num}", value="❌ Séquence incorrecte", inline=False)
        await update_embed(embed)
        return False

async def lancer_infusion(interaction, embed, update_embed, num):
    await interaction.channel.send("🔵 Prépare-toi à synchroniser ton Reiatsu...")
    await asyncio.sleep(2)
    msg = await interaction.channel.send("🔵")
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
        if u.bot or r.message.id != msg.id or str(r.emoji) != "⚡" or u != interaction.user:
            return False
        delta = (discord.utils.utcnow() - start).total_seconds()
        # Réaction entre 0.8 et 1.2s
        return 0.8 <= delta <= 1.2

    try:
        await interaction.client.wait_for("reaction_add", check=check, timeout=2)
        embed.add_field(name=f"Épreuve {num}", value="✅ Synchronisation réussie", inline=False)
        await update_embed(embed)
        return True
    except asyncio.TimeoutError:
        embed.add_field(name=f"Épreuve {num}", value="❌ Synchronisation ratée", inline=False)
        await update_embed(embed)
        return False

async def lancer_emoji9(interaction, embed, update_embed, num):
    groupes = [["🍎","🍅"],["☁️","🌥️"],["☘️","🍀"],["🌺","🌸"],["👜","💼"],["🌹","🌷"],
               ["🤞","✌️"],["✊","👊"],["😕","😐"],["🌟","⭐"],["🦝","🐨"],["🔒","🔓"],
               ["🏅","🥇"],["🌧️","🌨️"],["🐆","🐅"],["🙈","🙊"],["🐋","🐳"],["🐢","🐊"]]
    base, intrus = random.choice(groupes)
    has_intrus = random.choice([True, False])
    emojis = [base]*9
    if has_intrus:
        emojis[random.randint(0,8)] = intrus
    random.shuffle(emojis)
    ligne = "".join(emojis)

    await interaction.channel.send(f"🔎 {ligne}\nRéponds avec ✅ si tous identiques, ❌ sinon.")

    def check(r, u):
        return u == interaction.user and r.message.channel == interaction.channel and str(r.emoji) in ["✅", "❌"]

    try:
        r, u = await interaction.client.wait_for("reaction_add", check=check, timeout=15)
        success = (str(r.emoji) == "✅" and not has_intrus) or (str(r.emoji) == "❌" and has_intrus)
        msg = "✅ Bonne réponse" if success else "❌ Mauvaise réponse"
        embed.add_field(name=f"Épreuve {num}", value=msg, inline=False)
        await update_embed(embed)
        return success
    except asyncio.TimeoutError:
        embed.add_field(name=f"Épreuve {num}", value="⌛ Temps écoulé", inline=False)
        await update_embed(embed)
        return False

async def lancer_bmoji(interaction, embed, update_embed, num):
    characters = load_characters()
    pers = random.choice(characters)
    nom = pers["nom"]
    emojis = random.sample(pers["emojis"], k=min(3, len(pers["emojis"])))
    distracteurs = random.sample([c["nom"] for c in characters if c["nom"] != nom], 3)
    options = distracteurs + [nom]
    random.shuffle(options)
    lettres = ["🇦", "🇧", "🇨", "🇩"]
    bonne = lettres[options.index(nom)]

    desc = " ".join(emojis) + "\n"
    desc += "\n".join(f"{lettres[i]} : {options[i]}" for i in range(4))
    msg = await interaction.channel.send(f"🔍 Devine le perso :\n{desc}")

    for e in lettres:
        await msg.add_reaction(e)

    def check(r, u):
        return u == interaction.user and r.message.id == msg.id and str(r.emoji) in lettres

    try:
        r, u = await interaction.client.wait_for("reaction_add", check=check, timeout=30)
        success = (str(r.emoji) == bonne)
        msg = "✅ Bonne réponse" if success else "❌ Mauvaise réponse"
        embed.add_field(name=f"Épreuve {num}", value=msg, inline=False)
        await update_embed(embed)
        return success
    except asyncio.TimeoutError:
        embed.add_field(name=f"Épreuve {num}", value="⌛ Temps écoulé", inline=False)
        await update_embed(embed)
        return False

# ────────────────────────────────────────────────────────────────────────────────
# 🔁 Lancer 3 épreuves aléatoires dans le même embed
# ────────────────────────────────────────────────────────────────────────────────

TACHES = [
    lancer_emoji,
    lancer_reflexe,
    lancer_fleche,
    lancer_infusion,
    lancer_emoji9,
    lancer_bmoji,
]

async def lancer_3_taches(interaction, embed, update_embed):
    """Lance 3 épreuves aléatoires dans le même embed.
    Met à jour l'embed via update_embed après chaque épreuve.
    Retourne True si toutes réussies, False dès la première échec."""
    choisies = random.sample(TACHES, 3)
    for i, tache in enumerate(choisies, start=1):
        success = await tache(interaction, embed, update_embed, i)
        if not success:
            return False
    return True
