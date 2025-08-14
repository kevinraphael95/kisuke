# ────────────────────────────────────────────────────────────────────────────────
# 📌 utils/taches.py — Mini-jeux (tâches) pour le bot
# Objectif : Mini-jeux interactifs affichés dynamiquement dans un embed unique
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
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_emojis.json")
def load_characters():
    """Charge les personnages depuis le fichier JSON."""
    with open(DATA_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Fonctions des mini-jeux — version avec boutons
# ────────────────────────────────────────────────────────────────────────────────

async def lancer_emoji(interaction, embed, update_embed, num):
    pool = ["💀", "🌀", "🔥", "🌪️", "🌟", "🍥", "🍡", "🧊", "❄️", "💨"]
    sequence = random.sample(pool, 3)
    autres = [e for e in pool if e not in sequence]
    mix = sequence + random.sample(autres, 2)
    random.shuffle(mix)

    class EmojiButton(discord.ui.Button):
        def __init__(self, emoji):
            super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji)
            self.emoji_val = emoji

        async def callback(self, interaction_button):
            if interaction_button.user != interaction.user:
                return
            await interaction_button.response.defer()
            if len(view.reponses) < len(sequence) and self.emoji_val == sequence[len(view.reponses)]:
                view.reponses.append(self.emoji_val)
                if len(view.reponses) == len(sequence):
                    view.stop()
            else:
                view.reponses.clear()

    view = discord.ui.View(timeout=120)
    for e in mix:
        view.add_item(EmojiButton(e))
    view.reponses = []

    msg = await interaction.followup.send(f"🔁 Reproduis cette séquence : {' → '.join(sequence)}", view=view)
    view.message = msg
    await view.wait()

    success = view.reponses == sequence
    msg = "✅ Séquence réussie" if success else "❌ Échec de la séquence"
    embed.add_field(name=f"Épreuve {num}", value=msg, inline=False)
    await update_embed(embed)
    return success

async def lancer_reflexe(interaction, embed, update_embed, num):
    compte = ["5️⃣", "4️⃣", "3️⃣", "2️⃣", "1️⃣"]

    class ReflexeButton(discord.ui.Button):
        def __init__(self, emoji):
            super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji)
            self.emoji_val = emoji

        async def callback(self, interaction_button):
            if interaction_button.user != interaction.user:
                return
            await interaction_button.response.defer()
            if len(view.reponses) < len(compte) and self.emoji_val == compte[len(view.reponses)]:
                view.reponses.append(self.emoji_val)
                if len(view.reponses) == len(compte):
                    view.stop()
            else:
                view.reponses.clear()

    view = discord.ui.View(timeout=20)
    for e in compte:
        view.add_item(ReflexeButton(e))
    view.reponses = []

    msg = await interaction.followup.send("🕒 Clique dans l’ordre : `5️⃣ 4️⃣ 3️⃣ 2️⃣ 1️⃣`", view=view)
    view.message = msg
    await view.wait()

    success = view.reponses == compte
    msg = "⚡ Réflexe réussi" if success else "❌ Échec du réflexe"
    embed.add_field(name=f"Épreuve {num}", value=msg, inline=False)
    await update_embed(embed)
    return success

async def lancer_fleche(interaction, embed, update_embed, num):
    fleches = ["⬅️", "⬆️", "⬇️", "➡️"]
    sequence = [random.choice(fleches) for _ in range(5)]

    tmp = await interaction.channel.send(f"🧭 Mémorise : `{' '.join(sequence)}` (5 s)")
    await asyncio.sleep(5)
    await tmp.delete()

    class FlecheButton(discord.ui.Button):
        def __init__(self, emoji):
            super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji)
            self.emoji_val = emoji

        async def callback(self, interaction_button):
            if interaction_button.user != interaction.user:
                return
            await interaction_button.response.defer()
            if len(view.reponses) < len(sequence) and self.emoji_val == sequence[len(view.reponses)]:
                view.reponses.append(self.emoji_val)
                if len(view.reponses) == len(sequence):
                    view.stop()
            else:
                view.reponses.clear()

    view = discord.ui.View(timeout=30)
    for e in fleches:
        view.add_item(FlecheButton(e))
    view.reponses = []

    await interaction.channel.send("🔁 Reproduis la séquence :", view=view)
    await view.wait()

    success = view.reponses == sequence
    msg = "✅ Séquence fléchée réussie" if success else "❌ Séquence incorrecte"
    embed.add_field(name=f"Épreuve {num}", value=msg, inline=False)
    await update_embed(embed)
    return success

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

    bouton = discord.ui.Button(style=discord.ButtonStyle.danger, emoji="⚡")
    view = discord.ui.View(timeout=2)
    view.add_item(bouton)
    event = asyncio.Event()

    async def bouton_callback(inter_button):
        if inter_button.user == interaction.user:
            await inter_button.response.defer()
            now = discord.utils.utcnow()
            delta = (now - start).total_seconds()
            view.success = 0.8 <= delta <= 1.2
            event.set()

    bouton.callback = bouton_callback
    start = discord.utils.utcnow()

    await msg.edit(content="🔴 Cliquez ⚡ maintenant", view=view)
    try:
        await asyncio.wait_for(event.wait(), timeout=2)
    except asyncio.TimeoutError:
        view.success = False

    msg_res = "✅ Synchronisation réussie" if view.success else "❌ Synchronisation ratée"
    embed.add_field(name=f"Épreuve {num}", value=msg_res, inline=False)
    await update_embed(embed)
    return view.success

async def lancer_emoji9(interaction, embed, update_embed, num):
    groupes = [
        ["🍎","🍅"],["☁️","🌥️"],["☘️","🍀"],["🌺","🌸"],["👜","💼"],["🌹","🌷"],
        ["🤞","✌️"],["✊","👊"],["😕","😐"],["🌟","⭐"],["🦝","🐨"],["🔒","🔓"],
        ["🏅","🥇"],["🌧️","🌨️"],["🐆","🐅"],["🙈","🙊"],["🐋","🐳"],["🐢","🐊"]
    ]
    base, intrus = random.choice(groupes)
    has_intrus = random.choice([True, False])
    emojis = [base]*9
    if has_intrus:
        emojis[random.randint(0,8)] = intrus
    random.shuffle(emojis)
    ligne = "".join(emojis)

    class ChoixButton(discord.ui.Button):
        def __init__(self, label):
            super().__init__(label=label, style=discord.ButtonStyle.primary)

        async def callback(self, inter_button):
            if inter_button.user != interaction.user:
                return
            await inter_button.response.defer()
            choix = self.label
            success = (choix == "✅" and not has_intrus) or (choix == "❌" and has_intrus)
            view.success = success
            view.stop()

    view = discord.ui.View(timeout=15)
    view.add_item(ChoixButton("✅"))
    view.add_item(ChoixButton("❌"))
    view.success = False

    msg = await interaction.followup.send(f"🔎 {ligne}\nTous identiques ? (✅ oui / ❌ non)", view=view)
    view.message = msg
    await view.wait()

    msg = "✅ Bonne réponse" if view.success else "❌ Mauvaise réponse"
    embed.add_field(name=f"Épreuve {num}", value=msg, inline=False)
    await update_embed(embed)
    return view.success

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
    desc = " ".join(emojis) + "\n" + "\n".join(f"{lettres[i]} : {options[i]}" for i in range(4))

    class PersoButton(discord.ui.Button):
        def __init__(self, emoji, idx):
            super().__init__(emoji=emoji, style=discord.ButtonStyle.secondary)
            self.idx = idx

        async def callback(self, inter_button):
            if inter_button.user != interaction.user:
                return
            await inter_button.response.defer()
            view.success = (lettres[self.idx] == bonne)
            view.stop()

    view = discord.ui.View(timeout=30)
    for i in range(4):
        view.add_item(PersoButton(lettres[i], i))
    view.success = False

    msg = await interaction.followup.send(f"🔍 Devine le perso :\n{desc}", view=view)
    view.message = msg
    await view.wait()

    msg = "✅ Bonne réponse" if view.success else "❌ Mauvaise réponse"
    embed.add_field(name=f"Épreuve {num}", value=msg, inline=False)
    await update_embed(embed)
    return view.success

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
    """
    Lance 3 tâches aléatoires et affiche dynamiquement l’épreuve en cours
    dans un champ unique 'Épreuve en cours' de l'embed.
    """
    taches_disponibles = TACHES.copy()
    random.shuffle(taches_disponibles)
    selection = taches_disponibles[:3]
    success_global = True

    for i, tache in enumerate(selection):
        embed.set_field_at(0, name="Épreuve en cours", value=f"🔹 Épreuve {i+1} en cours...", inline=False)
        await update_embed(embed)
        try:
            result = await tache(interaction, embed, update_embed, i+1)
        except Exception:
            result = False
        if not result:
            success_global = False
            break

    return success_global

