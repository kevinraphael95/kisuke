# ────────────────────────────────────────────────────────────────────────────────
# 📌 kawashima_games.py — Mini-jeux Professeur Kawashima
# Objectif : Contient tous les mini-jeux cérébraux détectés automatiquement
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import random
import asyncio
import discord
from discord.ui import View, Button

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Paramètres
# ────────────────────────────────────────────────────────────────────────────────
TIMEOUT = 60  # 1 minute pour répondre à chaque mini-jeu

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Mini-jeux (chacun avec .emoji et .title)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧮 Addition à la suite
# ────────────────────────────────────────────────────────────────────────────────
async def addition_cachee(ctx, embed, get_user_id, bot):
    additions = [random.randint(-9, 9) for _ in range(6)]
    total = sum(additions)

    embed.clear_fields()
    embed.add_field(name="🧮 Additions à la suite", value="Observe bien les additions successives...", inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(3)

    for add in additions:
        embed.clear_fields()
        embed.add_field(name="🧮 Additions à la suite", value=f"{add:+d}", inline=False)
        await ctx.edit(embed=embed)
        await asyncio.sleep(1.8)

    embed.clear_fields()
    embed.add_field(name="🧮 Additions à la suite", value="Quel est le total final ?", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == total
    except:
        return False
addition_cachee.title = "Addition à la suite"
addition_cachee.emoji = "➕"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧮 Calcul rapide
# ────────────────────────────────────────────────────────────────────────────────
async def calcul_rapide(ctx, embed, get_user_id, bot):
    op = random.choice(["+", "-", "*", "/"])

    if op == "*":
        a = random.randint(1, 10)      # premier facteur
        b = random.randint(1, 10)      # deuxième facteur limité
        answer = a * b
    elif op == "/":
        b = random.randint(1, 10)      # diviseur limité
        answer = random.randint(1, 10) # résultat final limité
        a = b * answer                  # garantit que a / b est entier
    else:  # + ou -
        a = random.randint(10, 50)
        b = random.randint(10, 50)
        answer = eval(f"{a}{op}{b}")

    question = f"{a} {op} {b} = ?"

    embed.clear_fields()
    embed.add_field(name="🧮 Calcul rapide", value=question, inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == answer
    except:
        return False

calcul_rapide.title = "Calcul rapide"
calcul_rapide.emoji = "🧮"


# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🔢 Carré magique 3x3 fiable emoji
# ────────────────────────────────────────────────────────────────────────────────
async def carre_magique_fiable_emoji(ctx, embed, get_user_id, bot):
    import random

    # Base carré magique 3x3
    base = [
        [8, 1, 6],
        [3, 5, 7],
        [4, 9, 2]
    ]

    # Appliquer une rotation/symétrie aléatoire
    def rotate(square):
        return [list(x) for x in zip(*square[::-1])]  # rotation 90°

    def flip(square):
        return [row[::-1] for row in square]  # miroir horizontal

    for _ in range(random.randint(0, 3)):
        base = rotate(base)
    if random.choice([True, False]):
        base = flip(base)

    # Cacher un nombre
    row, col = random.randint(0, 2), random.randint(0, 2)
    answer = base[row][col]
    base[row][col] = "❓"

    # Conversion en emoji Discord
    num_to_emoji = {
        1: "1️⃣", 2: "2️⃣", 3: "3️⃣",
        4: "4️⃣", 5: "5️⃣", 6: "6️⃣",
        7: "7️⃣", 8: "8️⃣", 9: "9️⃣"
    }

    display = ""
    for r in base:
        display += "|".join(num_to_emoji.get(x, x) for x in r) + "\n"

    embed.clear_fields()
    embed.add_field(
        name="🔢 Carré magique",
        value=f"Complète le carré magique pour que toutes les lignes, colonnes et diagonales fassent 15 :\n{display}",
        inline=False
    )
    await ctx.edit(embed=embed)

    # Attente de la réponse
    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == answer
    except:
        return False

carre_magique_fiable_emoji.title = "Carré magique 3x3"
carre_magique_fiable_emoji.emoji = "🔢"

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Couleurs (Stroop visuel, réponse dans le chat)
# ────────────────────────────────────────────────────────────────────────────────
async def couleurs(ctx, bot):
    # Couleurs possibles et styles Discord
    styles = {
        "bleu": discord.ButtonStyle.primary,
        "vert": discord.ButtonStyle.success,
        "rouge": discord.ButtonStyle.danger,
        "gris": discord.ButtonStyle.secondary
    }

    # Choix aléatoire du mot et de sa couleur
    mot = random.choice(list(styles.keys())).upper()       # mot affiché
    couleur_vraie = random.choice(list(styles.keys()))     # couleur du bouton

    # Choix du type de question
    question_type = random.choice(["mot", "couleur"])
    if question_type == "mot":
        question_text = "Quel **MOT** est écrit sur le bouton ?"
        bonne_reponse = mot.lower()
    else:
        question_text = "Quelle est la **COULEUR** du bouton ?"
        bonne_reponse = couleur_vraie

    # Création du bouton visuel (désactivé)
    button = Button(label=mot, style=styles[couleur_vraie], disabled=True)
    view = View()
    view.add_item(button)

    # Création de l'embed
    embed = discord.Embed(
        title="🎨 Couleurs (Stroop)",
        description=f"Regarde le bouton ci-dessous :\n➡️ {question_text}",
        color=discord.Color.random()
    )

    # Envoi du message avec embed + bouton visuel
    await ctx.send(embed=embed, view=view)

    # Attente de la réponse dans le chat
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == ctx.author.id,
            timeout=60
        )
        return msg.content.lower().strip() == bonne_reponse
    except asyncio.TimeoutError:
        return False

# Métadonnées pour ton système
couleurs.title = "Couleurs"
couleurs.emoji = "🎨"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 📅 Datation (limité à ±1 semaine)
# ────────────────────────────────────────────────────────────────────────────────
async def datation(ctx, embed, get_user_id, bot):
    import datetime

    today = datetime.date.today()
    # Décalage aléatoire entre -7 et +7 jours
    delta_days = random.randint(-7, 7)
    date = today + datetime.timedelta(days=delta_days)
    
    jour = date.strftime("%A").lower()
    day, month, year = date.day, date.month, date.year

    embed.clear_fields()
    embed.add_field(
        name="📅 Datation",
        value=f"Quel jour de la semaine était le {day}/{month}/{year} ?",
        inline=False
    )
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return msg.content.lower().startswith(jour[:3])  # accepte "lun", "lundi", etc.
    except:
        return False

datation.title = "Datation"
datation.emoji = "📅"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🕒 Heures (version flexible)
# ────────────────────────────────────────────────────────────────────────────────
async def heures(ctx, embed, get_user_id, bot):
    # Génération aléatoire de deux heures
    h1, m1 = random.randint(0, 23), random.randint(0, 59)
    h2, m2 = random.randint(0, 23), random.randint(0, 59)

    # Calcul de la différence absolue en minutes
    diff = abs((h1 * 60 + m1) - (h2 * 60 + m2))
    hours, mins = divmod(diff, 60)

    # Formatage des heures en texte
    heure_1 = f"{h1:02d}:{m1:02d}"
    heure_2 = f"{h2:02d}:{m2:02d}"

    # Choix aléatoire du type d’énoncé
    question_type = random.choice([
        f"Quelle est la différence entre {heure_1} et {heure_2} ?",
        f"Combien de temps s’écoule entre {heure_1} et {heure_2} ?",
        f"De {heure_1} à {heure_2}, combien d’heures et de minutes passent ?",
        f"🕒 {heure_1} → {heure_2} = ?"
    ])

    # Petit bonus : parfois forcer l’ordre chronologique (pour un défi logique)
    if random.random() < 0.3 and h2 * 60 + m2 < h1 * 60 + m1:
        question_type += " (⚠️ passe par minuit)"

    embed.clear_fields()
    embed.add_field(name="🕒 Heures", value=question_type, inline=False)
    await ctx.edit(embed=embed)

    # Attente de la réponse
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        rep = msg.content.lower().replace("h", " ").replace(":", " ").replace("min", " ").replace("m", " ")
        nums = [int(x) for x in rep.split() if x.isdigit()]

        if len(nums) == 1:
            # Si l'utilisateur écrit seulement "90" → 90 minutes
            user_hours, user_mins = divmod(nums[0], 60)
        elif len(nums) >= 2:
            user_hours, user_mins = nums[0], nums[1]
        else:
            return False

        # Tolérance : accepter une marge d’erreur de ±1 minute
        diff_user = user_hours * 60 + user_mins
        diff_real = hours * 60 + mins
        return abs(diff_user - diff_real) <= 1

    except:
        return False

heures.title = "Heures"
heures.emoji = "🕒"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🔢 Mémoire numérique
# ────────────────────────────────────────────────────────────────────────────────
async def memoire_numerique(ctx, embed, get_user_id, bot):
    sequence = [random.randint(0, 9) for _ in range(6)]
    embed.clear_fields()
    embed.add_field(name="🔢 Mémoire numérique", value=str(sequence), inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(5)

    embed.clear_fields()
    embed.add_field(name="🔢 Mémoire numérique", value="🕵️‍♂️ Retape la séquence !", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return msg.content == "".join(map(str, sequence))
    except:
        return False
memoire_numerique.title = "Mémoire numérique"
memoire_numerique.emoji = "🔢"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 👁️ Mémoire visuelle (version boutons avec TIMEOUT global)
# ────────────────────────────────────────────────────────────────────────────────
async def memoire_visuelle(ctx, embed, get_user_id, bot):
    # Ensemble d'emojis
    base_emojis = ["🍎", "🚗", "🐶", "🌟", "⚽", "🎲", "💎", "🎵", "🍕", "🐱", "🚀", "🎁"]

    # Étape 1 : sélection des 4 emojis à mémoriser
    shown_emojis = random.sample(base_emojis, 4)
    embed.clear_fields()
    embed.add_field(
        name="👁️ Mémoire visuelle",
        value=f"Mémorise bien ces 4 emojis :\n{' '.join(shown_emojis)}",
        inline=False
    )
    await ctx.edit(embed=embed)

    # Temps pour mémoriser
    await asyncio.sleep(4)

    # Étape 2 : cacher la liste
    embed.clear_fields()
    embed.add_field(
        name="👁️ Mémoire visuelle",
        value="🔒 Les emojis ont disparu... retrouve celui qui **n'était PAS dans la liste !**",
        inline=False
    )
    await ctx.edit(embed=embed)

    # Petit délai aléatoire avant les boutons
    await asyncio.sleep(random.uniform(0.5, 1.5))

    # Étape 3 : préparation des boutons (les 4 + 1 intrus)
    all_choices = shown_emojis.copy()
    intrus = random.choice([e for e in base_emojis if e not in shown_emojis])
    all_choices.append(intrus)
    random.shuffle(all_choices)

    # Création de la vue avec boutons
    class EmojiView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=TIMEOUT)
            self.selected = None

    view = EmojiView()
    for e in all_choices:
        async def make_callback(emoji=e):
            async def callback(interaction: discord.Interaction):
                if interaction.user.id != get_user_id():
                    await interaction.response.send_message("🚫 Pas ton tour.", ephemeral=True)
                    return
                view.selected = emoji
                view.stop()
                await interaction.response.defer()
            return callback

        button = discord.ui.Button(label=e, style=discord.ButtonStyle.secondary)
        button.callback = await make_callback(e)
        view.add_item(button)

    msg = await ctx.edit(embed=embed, view=view)

    # Attente de la réponse
    await view.wait()

    # Vérifie la bonne réponse
    if not hasattr(view, "selected") or view.selected is None:
        return False    
    return view.selected == intrus
    
memoire_visuelle.title = "Mémoire visuelle"
memoire_visuelle.emoji = "👁️"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 💰 Monnaie
# ────────────────────────────────────────────────────────────────────────────────
async def monnaie(ctx, embed, get_user_id, bot):
    prix = random.randint(1, 20) + random.choice([0, 0.5, 0.2])
    donne = prix + random.choice([0.5, 1, 2])
    rendu = round(donne - prix, 2)

    embed.clear_fields()
    embed.add_field(name="💰 Monnaie", value=f"Prix : {prix:.2f} €\nPayé : {donne:.2f} €\n➡️ Quelle monnaie rends-tu ?", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return abs(float(msg.content.replace(',', '.')) - rendu) < 0.01
    except:
        return False
        
monnaie.title = "Monnaie"
monnaie.emoji = "💰"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🔤 Pagaille
# ────────────────────────────────────────────────────────────────────────────────
async def pagaille(ctx, embed, get_user_id, bot):
    mot = random.choice(["amour", "cerveau", "maison", "voiture", "banane"])
    melange = "".join(random.sample(mot, len(mot)))

    embed.clear_fields()
    embed.add_field(name="🔤 Pagaille", value=f"{melange}\n➡️ Remets les lettres dans l’ordre !", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return msg.content.lower() == mot
    except:
        return False
pagaille.title = "Pagaille"
pagaille.emoji = "🔤"

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Jeu : Paires cachées (Memory)
# ────────────────────────────────────────────────────────────────────────────────
class MemoryButton(Button):
    def __init__(self, emoji):
        super().__init__(style=discord.ButtonStyle.secondary, label="❓", row=0)
        self.emoji_hidden = emoji
        self.revealed = False
        self.matched = False


class MemoryView(View):
    def __init__(self, user_id, emojis, taille=4):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.taille = taille
        self.flipped = []
        self.total_pairs = (taille * taille) // 2
        self.found_pairs = 0

        # Créer les boutons (en 4x4)
        cards = emojis * 2
        random.shuffle(cards)
        for i in range(taille * taille):
            emoji = cards[i]
            btn = MemoryButton(emoji)
            btn.row = i // taille
            btn.custom_id = f"memory_{i}"
            btn.callback = self.on_button_click
            self.add_item(btn)

    async def on_button_click(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Ce jeu n’est pas pour toi 😅", ephemeral=True)
            return

        # Trouve le bouton correspondant
        button_id = interaction.data["custom_id"]
        btn = next((b for b in self.children if b.custom_id == button_id), None)
        if not btn or btn.matched or btn.revealed:
            return

        btn.label = btn.emoji_hidden
        btn.style = discord.ButtonStyle.primary
        btn.revealed = True
        self.flipped.append(btn)

        await interaction.response.edit_message(view=self)

        # Vérifie les paires
        if len(self.flipped) == 2:
            await asyncio.sleep(0.8)
            b1, b2 = self.flipped
            if b1.emoji_hidden == b2.emoji_hidden:
                b1.style = b2.style = discord.ButtonStyle.success
                b1.matched = b2.matched = True
                self.found_pairs += 1
            else:
                b1.label = b2.label = "❓"
                b1.style = b2.style = discord.ButtonStyle.secondary
                b1.revealed = b2.revealed = False
            self.flipped.clear()

            # Fin du jeu
            if self.found_pairs == self.total_pairs:
                for item in self.children:
                    item.disabled = True
                await interaction.edit_original_response(
                    content="🎉 **Bravo ! Toutes les paires trouvées !**",
                    view=self
                )
                self.stop()
            else:
                await interaction.edit_original_response(view=self)


async def paires_cachees(message, embed, get_user_id, bot, wait_for_prefixed_answer):
    """Mini-jeu : Trouve toutes les paires identiques en cliquant sur les cartes."""
    user_id = get_user_id()

    # Thèmes possibles 🎨
    themes = {
        "Fruits 🍓": ["🍎", "🍌", "🍇", "🍓", "🍒", "🍋", "🥝", "🍑"],
        "Animaux 🐾": ["🐶", "🐱", "🐰", "🦊", "🐻", "🐼", "🐸", "🐧"],
        "Objets ⚙️": ["⌚", "💡", "📱", "🎮", "🎲", "📷", "💎", "🎁"],
        "Visages 😄": ["😀", "😂", "🥶", "😡", "😎", "🥵", "🤓", "😴"]
    }
    theme_name, emojis = random.choice(list(themes.items()))

    embed.clear_fields()
    embed.title = "🧩 Paires cachées"
    embed.description = f"Trouve toutes les paires identiques !\n**Thème :** {theme_name}"
    embed.color = discord.Color.random()

    view = MemoryView(user_id, emojis, taille=4)
    await message.edit(embed=embed, view=view)

    # Attend la fin du jeu
    await view.wait()
    return view.found_pairs == view.total_pairs


# Métadonnées pour l’intégration dans la liste
paires_cachees.title = "Paires cachées"
paires_cachees.emoji = "🧩"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ⚡ Rapidité
# ────────────────────────────────────────────────────────────────────────────────
async def rapidite(ctx, embed, get_user_id, bot):
    nums = random.sample(range(10, 99), 5)
    mode = random.choice(["grand", "petit"])
    embed.clear_fields()
    embed.add_field(name="⚡ Rapidité", value=f"Trouve le plus {mode} : {', '.join(map(str, nums))}", inline=False)
    await ctx.edit(embed=embed)
    correct = max(nums) if mode == "grand" else min(nums)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == correct
    except:
        return False
rapidite.title = "Rapidité"
rapidite.emoji = "⚡"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ⚡ Réflexe couleur (cliquer quand le bouton devient vert)
# ────────────────────────────────────────────────────────────────────────────────
async def reflexe_couleur(ctx, embed, get_user_id, bot):
    embed.clear_fields()
    embed.add_field(
        name="⚡ Réflexe couleur",
        value="Appuie sur le bouton **dès qu'il devient vert**.\nMais pas avant 👀",
        inline=False
    )
    await ctx.edit(embed=embed)

    class ReflexeView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=7)
            self.clicked = False
            self.start_time = None
            self.reaction_time = None
            self.too_early = False

        @discord.ui.button(label="🔴 ATTENDS...", style=discord.ButtonStyle.danger)
        async def reflexe(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != get_user_id():
                await interaction.response.send_message("🚫 Ce n’est pas ton jeu.", ephemeral=True)
                return
            if button.style == discord.ButtonStyle.danger:
                self.too_early = True
                self.clicked = True
                self.stop()
                await interaction.response.send_message("❌ Trop tôt !", ephemeral=True)
            elif button.style == discord.ButtonStyle.success:
                self.reaction_time = round(asyncio.get_event_loop().time() - self.start_time, 3)
                self.clicked = True
                self.stop()
                await interaction.response.send_message(f"✅ Réflexe en {self.reaction_time}s !", ephemeral=True)

    view = ReflexeView()
    msg = await ctx.edit(view=view)

    # Attente aléatoire avant passage au vert
    await asyncio.sleep(random.uniform(2, 5))
    if view.is_finished():
        return False  # déjà cliqué trop tôt

    # Passage au vert
    button = view.children[0]
    button.label = "🟢 CLIQUE !"
    button.style = discord.ButtonStyle.success
    await msg.edit(view=view)
    view.start_time = asyncio.get_event_loop().time()

    # Attente du clic
    await view.wait()

    if view.too_early or not view.clicked or view.reaction_time is None:
        return False

    # Réussite si temps < 1.2s
    return view.reaction_time < 1.2

# Métadonnées pour ton système
reflexe_couleur.title = "Réflexe couleur"
reflexe_couleur.emoji = "🟢"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧩 Suite alphabétique (sens aléatoire)
# ────────────────────────────────────────────────────────────────────────────────
async def suite_alpha(ctx, embed, get_user_id, bot):
    sens_normal = random.choice([True, False])

    if sens_normal:
        start = random.randint(65, 70)  # A-F
        step = random.randint(1, 3)
        serie = [chr(start + i * step) for i in range(4)]
        answer = chr(start + 4 * step)
    else:
        start = random.randint(85, 90)  # U-Z
        step = random.randint(1, 3)
        serie = [chr(start - i * step) for i in range(4)]
        answer = chr(start - 4 * step)

    embed.clear_fields()
    embed.add_field(
        name="🧩 Suite alphabétique",
        value=f"{', '.join(serie)} ... ?",
        inline=False
    )
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return msg.content.strip().upper() == answer
    except:
        return False

suite_alpha.title = "Suite alphabétique"
suite_alpha.emoji = "🧩"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ➗ Suite logique (version enrichie)
# ────────────────────────────────────────────────────────────────────────────────
async def suite_logique(ctx, embed, get_user_id, bot):
    type_suite = random.choice(["arithmétique", "géométrique", "alternée", "carrés", "fibonacci"])
    serie = []
    answer_index = None
    answer = None

    # Génération de la série selon le type
    if type_suite == "arithmétique":
        start = random.randint(1, 10)
        step = random.randint(2, 6)
        serie = [start + i * step for i in range(5)]

    elif type_suite == "géométrique":
        start = random.randint(1, 5)
        ratio = random.randint(2, 3)
        serie = [start * (ratio ** i) for i in range(5)]

    elif type_suite == "alternée":
        start = random.randint(1, 10)
        add, sub = random.randint(2, 5), random.randint(1, 4)
        serie = [start]
        for i in range(1, 5):
            if i % 2 == 1:
                serie.append(serie[-1] + add)
            else:
                serie.append(serie[-1] - sub)

    elif type_suite == "carrés":
        start = random.randint(1, 5)
        serie = [i ** 2 for i in range(start, start + 5)]

    elif type_suite == "fibonacci":
        a, b = random.randint(1, 5), random.randint(1, 5)
        serie = [a, b]
        for _ in range(3):
            serie.append(serie[-1] + serie[-2])

    # Choisir une position aléatoire à remplacer par "?"
    answer_index = random.randint(0, len(serie) - 1)
    answer = serie[answer_index]
    display_serie = serie.copy()
    display_serie[answer_index] = "?"

    # Affichage
    embed.clear_fields()
    embed.add_field(
        name="➗ Suite logique",
        value=f"{display_serie} ... ?",
        inline=False
    )
    await ctx.edit(embed=embed)

    # Attente de la réponse
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return int(msg.content) == answer
    except:
        return False

suite_logique.title = "Suite logique"
suite_logique.emoji = "➗"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🔁 Symétrie
# ────────────────────────────────────────────────────────────────────────────────
async def symetrie(ctx, embed, get_user_id, bot):
    symbols = [">", "<", "*", "#"]
    seq = "".join(random.choices(symbols, k=5))
    mirror = seq[::-1].translate(str.maketrans("><", "<>"))

    embed.clear_fields()
    embed.add_field(name="🔁 Symétrie", value=f"Séquence : {seq}\n➡️ Tape la version miroir :", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return msg.content.strip() == mirror
    except:
        return False
symetrie.title = "Symétrie"
symetrie.emoji = "🔁"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🔎 Trouver la différence
# ────────────────────────────────────────────────────────────────────────────────
async def trouver_difference(ctx, embed, get_user_id, bot):
    liste1 = [random.randint(1, 9) for _ in range(5)]
    liste2 = liste1.copy()
    index = random.randint(0, 4)
    liste2[index] = random.randint(10, 20)

    embed.clear_fields()
    embed.add_field(name="🔎 Trouver la différence", value=f"{liste2}\nQuelle position diffère (1-5) ?", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == index + 1
    except:
        return False
trouver_difference.title = "Trouver la différence"
trouver_difference.emoji = "🔎"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🔍 Trouver l’intrus (version améliorée)
# ────────────────────────────────────────────────────────────────────────────────
async def trouver_intrus(ctx, embed, get_user_id, bot):
    # Groupes thématiques
    animaux = ["chien", "chat", "lapin", "poisson", "cheval", "oiseau"]
    fruits = ["pomme", "banane", "orange", "kiwi", "fraise", "raisin"]
    objets = ["stylo", "chaise", "livre", "voiture", "table", "lampe"]
    couleurs = ["rouge", "bleu", "vert", "jaune", "noir", "blanc"]
    sports = ["foot", "tennis", "basket", "natation", "golf", "rugby"]

    groupes = [animaux, fruits, objets, couleurs, sports]

    # Choisir un groupe principal et un intrus d’un autre groupe
    principal = random.choice(groupes)
    autres = [g for g in groupes if g != principal]
    intrus = random.choice(random.choice(autres))

    # Construire la liste finale (3 du groupe principal + 1 intrus)
    mots = random.sample(principal, 3) + [intrus]
    random.shuffle(mots)

    # Affichage
    embed.clear_fields()
    embed.add_field(
        name="🔍 Trouver l’intrus",
        value=f"{', '.join(mots)}\n➡️ Quel mot ne correspond pas aux autres ?",
        inline=False
    )
    await ctx.edit(embed=embed)

    # Attente de la réponse
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return msg.content.lower().strip() == intrus.lower()
    except:
        return False

trouver_intrus.title = "Trouver l’intrus"
trouver_intrus.emoji = "🔍"


# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ✏️ Typographie erreur
# ────────────────────────────────────────────────────────────────────────────────
async def typo_trap(ctx, embed, get_user_id, bot):
    mot = random.choice(["chien", "maison", "voiture", "ordinateur", "banane", "chocolat"])
    typo_index = random.randint(0, len(mot) - 1)
    mot_mod = list(mot)

    # Génère une lettre différente de la lettre originale
    original = mot_mod[typo_index]
    nouvelle_lettre = random.choice([chr(i) for i in range(97, 123) if chr(i) != original])
    mot_mod[typo_index] = nouvelle_lettre
    mot_mod = "".join(mot_mod)

    embed.clear_fields()
    embed.add_field(
        name="✏️ Typographie erreur",
        value=f"{mot_mod}\n➡️ Quelle lettre est incorrecte dans ce mot ? (ex: 'x')",
        inline=False
    )
    await ctx.edit(embed=embed)

    # Attente de la réponse
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return msg.content.lower().strip() == nouvelle_lettre
    except:
        return False

typo_trap.title = "Typographie erreur"
typo_trap.emoji = "✏️"




# the end
