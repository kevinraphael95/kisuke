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
# 🔹 Fonctions des mini-jeux — version boutons intégrés à l'embed
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

        async def callback(self, inter_button):
            if inter_button.user != interaction.user:
                return
            await inter_button.response.defer()
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

    # Affiche la séquence dans l'embed principal
    embed.set_field_at(0, name=f"Épreuve {num}", value=f"🔁 Reproduis cette séquence : {' → '.join(sequence)}", inline=False)
    await update_embed(embed)

    # Attache les boutons au message existant
    await interaction.edit_original_message(view=view)
    await view.wait()

    success = view.reponses == sequence
    msg = "✅ Séquence réussie" if success else "❌ Échec de la séquence"
    embed.set_field_at(0, name=f"Épreuve {num}", value=msg, inline=False)
    await update_embed(embed)
    return success

async def lancer_reflexe(interaction, embed, update_embed, num):
    compte = ["5️⃣", "4️⃣", "3️⃣", "2️⃣", "1️⃣"]

    class ReflexeButton(discord.ui.Button):
        def __init__(self, emoji):
            super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji)
            self.emoji_val = emoji

        async def callback(self, inter_button):
            if inter_button.user != interaction.user:
                return
            await inter_button.response.defer()
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

    embed.set_field_at(0, name=f"Épreuve {num}", value="🕒 Clique dans l’ordre : `5️⃣ 4️⃣ 3️⃣ 2️⃣ 1️⃣`", inline=False)
    await update_embed(embed)
    await interaction.edit_original_message(view=view)
    await view.wait()

    success = view.reponses == compte
    msg = "⚡ Réflexe réussi" if success else "❌ Échec du réflexe"
    embed.set_field_at(0, name=f"Épreuve {num}", value=msg, inline=False)
    await update_embed(embed)
    return success

async def lancer_fleche(interaction, embed, update_embed, num):
    fleches = ["⬅️", "⬆️", "⬇️", "➡️"]
    sequence = [random.choice(fleches) for _ in range(5)]

    embed.set_field_at(0, name=f"Épreuve {num}", value=f"🧭 Mémorise : `{' '.join(sequence)}` (5 s)", inline=False)
    await update_embed(embed)
    await asyncio.sleep(5)
    embed.set_field_at(0, name=f"Épreuve {num}", value="🔁 Reproduis la séquence avec les boutons ci-dessous :", inline=False)
    await update_embed(embed)

    class FlecheButton(discord.ui.Button):
        def __init__(self, emoji):
            super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji)
            self.emoji_val = emoji

        async def callback(self, inter_button):
            if inter_button.user != interaction.user:
                return
            await inter_button.response.defer()
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

    await interaction.edit_original_message(view=view)
    await view.wait()

    success = view.reponses == sequence
    msg = "✅ Séquence fléchée réussie" if success else "❌ Séquence incorrecte"
    embed.set_field_at(0, name=f"Épreuve {num}", value=msg, inline=False)
    await update_embed(embed)
    return success

# ────────────────────────────────────────────────────────────────────────────────
# 🔁 Lancer 3 épreuves aléatoires dans le même embed
# ────────────────────────────────────────────────────────────────────────────────
TACHES = [lancer_emoji, lancer_reflexe, lancer_fleche]  # tu peux rajouter les autres

async def lancer_3_taches(interaction, embed, update_embed):
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


# ────────────────────────────────────────────────────────────────────────────────
# 🔁 Lancer une épreuve unique
# ────────────────────────────────────────────────────────────────────────────────
async def lancer_tache_unique(interaction, nom_tache: str):
    """
    Lance une tâche précise par son nom (ex: 'reflexe').
    Utilisé par la commande !testtache /slash testtache.
    """
    nom_tache = nom_tache.lower()
    if nom_tache not in NOM_TACHES:
        if isinstance(interaction, discord.Interaction):
            await interaction.response.send_message(
                f"❌ Tâche inconnue : `{nom_tache}`.\nTâches dispo : {', '.join(NOM_TACHES.keys())}",
                ephemeral=True
            )
        else:
            await interaction.send(
                f"❌ Tâche inconnue : `{nom_tache}`.\nTâches dispo : {', '.join(NOM_TACHES.keys())}"
            )
        return False

    # Embed de suivi (comme dans lancer_3_taches)
    embed = discord.Embed(title=f"🔹 Test tâche : {nom_tache}", color=discord.Color.blurple())
    embed.add_field(name="Épreuve en cours", value="Chargement...", inline=False)

    if isinstance(interaction, discord.Interaction):
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
    else:
        message = await interaction.send(embed=embed)

    async def update_embed(new_embed):
        await message.edit(embed=new_embed)

    # Lancer la tâche choisie
    try:
        result = await NOM_TACHES[nom_tache](interaction, embed, update_embed, 1)
    except Exception as e:
        result = False
        embed.add_field(name="Erreur", value=f"⚠️ {e}", inline=False)
        await update_embed(embed)

    return result
