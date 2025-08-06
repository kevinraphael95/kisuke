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
# 📂 Chargement des données JSON (exemple)
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_emojis.json")

def load_characters():
    """Charge les personnages depuis le fichier JSON."""
    with open(DATA_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Fonctions des mini-jeux — version avec boutons
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

    class EmojiButton(discord.ui.Button):
        def __init__(self, emoji):
            super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji)
            self.emoji_val = emoji
        async def callback(self, interaction_button):
            if interaction_button.user != interaction.user:
                return
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
    tmp = await interaction.channel.send(f"🧭 Mémorise : `{' '.join(sequence)}` (5 s)")
    await asyncio.sleep(5)
    await tmp.delete()

    class FlecheButton(discord.ui.Button):
        def __init__(self, emoji):
            super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji)
            self.emoji_val = emoji
        async def callback(self, interaction_button):
            if interaction_button.user != interaction.user:
                return
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
            now = discord.utils.utcnow()
            delta = (now - start).total_seconds()
            if 0.8 <= delta <= 1.2:
                view.success = True
            else:
                view.success = False
            event.set()
            await inter_button.response.defer()

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
            choix = self.label
            success = (choix == "✅" and not has_intrus) or (choix == "❌" and has_intrus)
            view.success = success
            view.stop()

    view = discord.ui.View(timeout=15)
    view.add_item(ChoixButton("✅"))
    view.add_item(ChoixButton("❌"))
    view.success = False

    await interaction.followup.send(f"🧐 Trouve l'intrus ?\n{ligne}", view=view)
    await view.wait()

    msg_res = "✅ Bonne réponse !" if view.success else "❌ Mauvaise réponse"
    embed.add_field(name=f"Épreuve {num}", value=msg_res, inline=False)
    await update_embed(embed)
    return view.success


async def lancer_nim(interaction, embed, update_embed, num):
    tas = [1,3,5,7]

    class NimView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=60)
            self.tas = tas.copy()
            self.game_over = False
            self.winner = None

        def render(self):
            lines = []
            for i, t in enumerate(self.tas):
                lines.append(f"**Tas {i+1}** : " + "●"*t)
            return "\n".join(lines)

        async def update_message(self, interaction):
            content = f"NIM — C'est ton tour, {interaction.user.mention}.\n\n{self.render()}"
            await interaction.response.edit_message(content=content, view=self)

        @discord.ui.button(label="Tas 1 - Retirer 1", style=discord.ButtonStyle.secondary)
        async def tas1(self, button, interaction):
            await self.jouer(interaction, 0, 1)

        @discord.ui.button(label="Tas 1 - Retirer 2", style=discord.ButtonStyle.secondary)
        async def tas1b(self, button, interaction):
            await self.jouer(interaction, 0, 2)

        @discord.ui.button(label="Tas 2 - Retirer 1", style=discord.ButtonStyle.secondary)
        async def tas2(self, button, interaction):
            await self.jouer(interaction, 1, 1)

        @discord.ui.button(label="Tas 2 - Retirer 2", style=discord.ButtonStyle.secondary)
        async def tas2b(self, button, interaction):
            await self.jouer(interaction, 1, 2)

        @discord.ui.button(label="Tas 3 - Retirer 1", style=discord.ButtonStyle.secondary)
        async def tas3(self, button, interaction):
            await self.jouer(interaction, 2, 1)

        @discord.ui.button(label="Tas 3 - Retirer 2", style=discord.ButtonStyle.secondary)
        async def tas3b(self, button, interaction):
            await self.jouer(interaction, 2, 2)

        @discord.ui.button(label="Tas 4 - Retirer 1", style=discord.ButtonStyle.secondary)
        async def tas4(self, button, interaction):
            await self.jouer(interaction, 3, 1)

        @discord.ui.button(label="Tas 4 - Retirer 2", style=discord.ButtonStyle.secondary)
        async def tas4b(self, button, interaction):
            await self.jouer(interaction, 3, 2)

        async def jouer(self, interaction, tas_index, nombre):
            if interaction.user != interaction.message.interaction.user:
                await interaction.response.defer()
                return
            if self.tas[tas_index] < nombre:
                await interaction.response.defer()
                return
            self.tas[tas_index] -= nombre
            if sum(self.tas) == 0:
                self.game_over = True
                self.winner = interaction.user
                self.stop()
                await interaction.response.edit_message(content=f"🎉 {interaction.user.mention} a gagné le NIM !", view=None)
            else:
                await self.update_message(interaction)

    view = NimView()
    await interaction.followup.send("🎲 Jeu du NIM : retirez 1 ou 2 jetons d’un tas à votre tour.", view=view)
    await view.wait()
    success = getattr(view, "winner", None) == interaction.user
    msg_res = "✅ Tu as gagné !" if success else "❌ Tu as perdu ou abandonné."
    embed.add_field(name=f"Épreuve {num}", value=msg_res, inline=False)
    await update_embed(embed)
    return success

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Liste des épreuves disponibles (nom, fonction)
# ────────────────────────────────────────────────────────────────────────────────

TACHES = [
    ("Emoji", lancer_emoji),
    ("Réflexe", lancer_reflexe),
    ("Flèche", lancer_fleche),
    ("Infusion", lancer_infusion),
    ("Emoji 9", lancer_emoji9),
    ("NIM", lancer_nim),
]
