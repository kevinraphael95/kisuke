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
    await asyncio.sleep(3)  # prep_time

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
addition_cachee.prep_time = 3 + 1.8 * 6  # temps total avant question

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧮 Calcul rapide
# ────────────────────────────────────────────────────────────────────────────────
async def calcul_rapide(ctx, embed, get_user_id, bot):
    op = random.choice(["+", "-", "*", "/"])
    if op == "*":
        a, b = random.randint(1, 10), random.randint(1, 10)
        answer = a * b
    elif op == "/":
        b = random.randint(1, 10)
        answer = random.randint(1, 10)
        a = b * answer
    else:
        a, b = random.randint(10, 50), random.randint(10, 50)
        answer = eval(f"{a}{op}{b}")

    embed.clear_fields()
    embed.add_field(name="🧮 Calcul rapide", value=f"{a} {op} {b} = ?", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == answer
    except:
        return False

calcul_rapide.title = "Calcul rapide"
calcul_rapide.emoji = "🧮"
calcul_rapide.prep_time = 0

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🔢 Carré magique 3x3 fiable emoji
# ────────────────────────────────────────────────────────────────────────────────
async def carre_magique_fiable_emoji(ctx, embed, get_user_id, bot):
    base = [
        [8, 1, 6],
        [3, 5, 7],
        [4, 9, 2]
    ]

    def rotate(square):
        return [list(x) for x in zip(*square[::-1])]

    def flip(square):
        return [row[::-1] for row in square]

    for _ in range(random.randint(0, 3)):
        base = rotate(base)
    if random.choice([True, False]):
        base = flip(base)

    row, col = random.randint(0, 2), random.randint(0, 2)
    answer = base[row][col]
    base[row][col] = "❓"

    num_to_emoji = {i: f"{i}\u20e3" for i in range(1, 10)}

    display = "\n".join("|".join(num_to_emoji.get(x, x) for x in r) for r in base)

    embed.clear_fields()
    embed.add_field(
        name="🔢 Carré magique",
        value=f"Complète le carré magique pour que toutes les lignes, colonnes et diagonales fassent 15 :\n{display}",
        inline=False
    )
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == answer
    except:
        return False

carre_magique_fiable_emoji.title = "Carré magique 3x3"
carre_magique_fiable_emoji.emoji = "🔢"
carre_magique_fiable_emoji.prep_time = 0

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 👀 Compter les emojis
# ────────────────────────────────────────────────────────────────────────────────
async def compter_emojis(ctx, embed, get_user_id, bot):
    import random

    emojis = ["🍎", "🍌", "🍒", "🍇", "🍊"]
    cible = random.choice(emojis)

    # Génère une grille 4x4
    grille = [[random.choice(emojis) for _ in range(4)] for _ in range(4)]
    texte_grille = "\n".join("".join(ligne) for ligne in grille)

    # Compte combien de fois l'emoji cible apparaît
    total = sum(ligne.count(cible) for ligne in grille)

    embed.clear_fields()
    embed.add_field(
        name="👀 Compter les emojis",
        value=f"{texte_grille}\n\n➡️ Combien de {cible} dans cette grille ?",
        inline=False
    )
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return msg.content.isdigit() and int(msg.content) == total
    except:
        return False

compter_emojis.title = "Compter les emojis"
compter_emojis.emoji = "👀"
compter_emojis.prep_time = 1.5

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Couleurs (Stroop complet)
# ────────────────────────────────────────────────────────────────────────────────
async def couleurs(ctx, embed, get_user_id, bot):
    styles = {
        "bleu": discord.ButtonStyle.primary,
        "vert": discord.ButtonStyle.success,
        "rouge": discord.ButtonStyle.danger,
        "gris": discord.ButtonStyle.secondary
    }

    couleurs_list = list(styles.keys())
    mots = couleurs_list.copy()
    random.shuffle(mots)

    buttons = []
    for couleur, mot in zip(couleurs_list, mots):
        button = Button(label=mot.upper(), style=styles[couleur])
        buttons.append(button)

    question_type = random.choice(["mot", "couleur"])
    if question_type == "mot":
        cible = random.choice(mots)
        question = f"Appuie sur le bouton où est écrit le **MOT** `{cible.upper()}` !"
        condition = lambda b: b.label.lower() == cible
    else:
        cible = random.choice(couleurs_list)
        question = f"Appuie sur le bouton de **COULEUR** `{cible.upper()}` !"
        condition = lambda b: b.style == styles[cible]

    view = View(timeout=TIMEOUT)
    for button in buttons:
        async def callback(interaction, b=button):
            if interaction.user.id != get_user_id():
                await interaction.response.send_message("🚫 Ce jeu n’est pas pour toi !", ephemeral=True)
                return
            view.value = condition(b)
            view.stop()
            await interaction.response.defer()

        button.callback = callback
        view.add_item(button)

    embed.clear_fields()
    embed.add_field(name="🎨 Couleurs (Stroop)", value=question, inline=False)
    await ctx.edit(embed=embed, view=view)

    await asyncio.sleep(0.5)  # prep_time
    await view.wait()
    for child in view.children:
        child.disabled = True
    await ctx.edit(view=view)

    return getattr(view, "value", False)

couleurs.title = "Couleurs"
couleurs.emoji = "🎨"
couleurs.prep_time = 0.5

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 📅 Datation
# ────────────────────────────────────────────────────────────────────────────────
async def datation(ctx, embed, get_user_id, bot):
    import datetime

    today = datetime.date.today()
    delta_days = random.randint(-7, 7)
    date = today + datetime.timedelta(days=delta_days)
    
    jours_fr = {
        "Monday": "lundi",
        "Tuesday": "mardi",
        "Wednesday": "mercredi",
        "Thursday": "jeudi",
        "Friday": "vendredi",
        "Saturday": "samedi",
        "Sunday": "dimanche"
    }
    jour_complet = jours_fr[date.strftime("%A")]
    jour_abr = jour_complet[:3]

    embed.clear_fields()
    embed.add_field(
        name="📅 Datation",
        value=f"Quel jour de la semaine était le {date.day}/{date.month}/{date.year} ?",
        inline=False
    )
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        reponse = msg.content.lower().strip()
        return reponse == jour_complet or reponse == jour_abr
    except:
        return False

datation.title = "Datation"
datation.emoji = "📅"
datation.prep_time = 0

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧭 Directions opposées
# ────────────────────────────────────────────────────────────────────────────────
async def directions_opposees(ctx, embed, get_user_id, bot):
    import random
    from discord import ButtonStyle
    from discord.ui import View, Button

    # Flèches et opposés simples
    arrows = ["⬆️", "⬇️", "⬅️", "➡️"]
    opposites = {
        "⬆️": "⬇️",
        "⬇️": "⬆️",
        "⬅️": "➡️",
        "➡️": "⬅️"
    }

    # Choix aléatoire de la flèche
    arrow = random.choice(arrows)
    correct = opposites[arrow]

    # Affichage de la consigne
    embed.clear_fields()
    embed.add_field(
        name="🧭 Directions opposées",
        value=f"Flèche affichée : {arrow}\n➡️ Clique sur **la direction opposée** le plus vite possible !",
        inline=False
    )
    await ctx.edit(embed=embed)

    # Vue avec les boutons
    view = View(timeout=TIMEOUT)
    for symbol in arrows:
        async def button_callback(interaction, s=symbol):
            if interaction.user.id != get_user_id():
                return
            view.stop()
            view.result = (s == correct)
            await interaction.response.defer()

        btn = Button(label=symbol, style=ButtonStyle.secondary)
        btn.callback = button_callback
        view.add_item(btn)

    msg = await ctx.send(view=view)
    await view.wait()
    await msg.edit(view=None)
    return getattr(view, "result", False)

directions_opposees.title = "Directions opposées"
directions_opposees.emoji = "🧭"
directions_opposees.prep_time = 1

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ➗ Équation à trou
# ────────────────────────────────────────────────────────────────────────────────
async def equation_trou(ctx, embed, get_user_id, bot):
    op = random.choice(["+", "-", "*"])
    if op == "+":
        a, b = random.randint(1, 20), random.randint(1, 20)
        answer = random.choice([a, b])
        question = f"? + {b} = {a + b}" if answer == a else f"{a} + ? = {a + b}"
    elif op == "-":
        a, b = random.randint(10, 30), random.randint(1, 10)
        answer = random.choice([a, b])
        question = f"? - {b} = {a - b}" if answer == a else f"{a} - ? = {a - b}"
    else:
        a, b = random.randint(1, 10), random.randint(1, 10)
        answer = random.choice([a, b])
        question = f"? × {b} = {a * b}" if answer == a else f"{a} × ? = {a * b}"

    embed.clear_fields()
    embed.add_field(name="➗ Équation à trou", value=question, inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == answer
    except:
        return False

equation_trou.title = "Equation à trou"
equation_trou.emoji = "➗"
equation_trou.prep_time = 0

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🕒 Heures
# ────────────────────────────────────────────────────────────────────────────────
async def heures(ctx, embed, get_user_id, bot):
    h1, m1 = random.randint(0, 23), random.randint(0, 59)
    h2, m2 = random.randint(0, 23), random.randint(0, 59)
    diff = abs((h1 * 60 + m1) - (h2 * 60 + m2))
    hours, mins = divmod(diff, 60)

    heure_1, heure_2 = f"{h1:02d}:{m1:02d}", f"{h2:02d}:{m2:02d}"
    question_type = f"Quelle est la différence entre {heure_1} et {heure_2} ?"

    embed.clear_fields()
    embed.add_field(name="🕒 Heures", value=question_type, inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        rep = msg.content.lower().replace("h", " ").replace(":", " ").replace("min", " ").replace("m", " ")
        nums = [int(x) for x in rep.split() if x.isdigit()]
        if len(nums) == 1:
            user_hours, user_mins = divmod(nums[0], 60)
        elif len(nums) >= 2:
            user_hours, user_mins = nums[0], nums[1]
        else:
            return False
        diff_user = user_hours * 60 + user_mins
        diff_real = hours * 60 + mins
        return abs(diff_user - diff_real) <= 1
    except:
        return False

heures.title = "Heures"
heures.emoji = "🕒"
heures.prep_time = 0

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🔢 Mémoire numérique
# ────────────────────────────────────────────────────────────────────────────────
async def memoire_numerique(ctx, embed, get_user_id, bot):
    sequence = [random.randint(0, 9) for _ in range(6)]
    embed.clear_fields()
    embed.add_field(name="🔢 Mémoire numérique", value=str(sequence), inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(5)  # prep_time

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
memoire_numerique.prep_time = 5

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 👁️ Mémoire visuelle (boutons)
# ────────────────────────────────────────────────────────────────────────────────
async def memoire_visuelle(ctx, embed, get_user_id, bot):
    prep_time = 4
    base_emojis = ["🍎", "🚗", "🐶", "🌟", "⚽", "🎲", "💎", "🎵", "🍕", "🐱", "🚀", "🎁"]
    shown_emojis = random.sample(base_emojis, 4)

    embed.clear_fields()
    embed.add_field(
        name="👁️ Mémoire visuelle",
        value=f"Mémorise bien ces 4 emojis :\n{' '.join(shown_emojis)}",
        inline=False
    )
    await ctx.edit(embed=embed)
    await asyncio.sleep(prep_time)

    embed.clear_fields()
    embed.add_field(
        name="👁️ Mémoire visuelle",
        value="🔒 Les emojis ont disparu... retrouve celui qui **n'était PAS dans la liste !**",
        inline=False
    )
    await ctx.edit(embed=embed)
    await asyncio.sleep(1)

    all_choices = shown_emojis.copy()
    intrus = random.choice([e for e in base_emojis if e not in shown_emojis])
    all_choices.append(intrus)
    random.shuffle(all_choices)

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

    await ctx.edit(embed=embed, view=view)
    await view.wait()
    return getattr(view, "selected", None) == intrus

memoire_visuelle.title = "Mémoire visuelle"
memoire_visuelle.emoji = "👁️"
memoire_visuelle.prep_time = 4

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 💰 Monnaie
# ────────────────────────────────────────────────────────────────────────────────
async def monnaie(ctx, embed, get_user_id, bot):
    prep_time = 2
    prix = random.randint(1, 20) + random.choice([0, 0.5, 0.2])
    donne = prix + random.choice([0.5, 1, 2])
    rendu = round(donne - prix, 2)

    embed.clear_fields()
    embed.add_field(
        name="💰 Monnaie",
        value=f"Prix : {prix:.2f} €\nPayé : {donne:.2f} €\n➡️ Quelle monnaie rends-tu ?",
        inline=False
    )
    await ctx.edit(embed=embed)
    await asyncio.sleep(prep_time)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return abs(float(msg.content.replace(',', '.')) - rendu) < 0.01
    except:
        return False

monnaie.title = "Monnaie"
monnaie.emoji = "💰"
monnaie.prep_time = 2

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🔁 Mot miroir
# ────────────────────────────────────────────────────────────────────────────────
async def mot_miroir(ctx, embed, get_user_id, bot):
    prep_time = 2
    mots = ["maison", "cerveau", "banane", "ordinateur", "voiture"]
    mot = random.choice(mots)
    mot_inverse = mot[::-1]

    embed.clear_fields()
    embed.add_field(
        name="🔁 Mot miroir",
        value=f"Tape ce mot à l'envers : {mot}",
        inline=False
    )
    await ctx.edit(embed=embed)
    await asyncio.sleep(prep_time)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return msg.content.lower() == mot_inverse
    except:
        return False

mot_miroir.title = "Mot miroir"
mot_miroir.emoji = "🔁"
mot_miroir.prep_time = 2

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧊 Ombre
# ────────────────────────────────────────────────────────────────────────────────
async def ombre(ctx, embed, get_user_id, bot):
    prep_time = 2
    emojis = ["◼️", "◾", "▪️", "⬛"]  # du plus gros au plus petit environ

    # On choisit aléatoirement s’il faut trouver le plus grand ou le plus petit
    mode = random.choice(["grand", "petit"])
    base = random.choice(emojis[1:3])  # symbole de base moyen
    grid_size = 4

    # On construit une grille de base
    grid = [[base for _ in range(grid_size)] for _ in range(grid_size)]

    # On remplace une case par une taille différente
    if mode == "grand":
        special = emojis[0]  # plus gros
    else:
        special = emojis[-1]  # plus petit
    special_pos = (random.randint(0, grid_size - 1), random.randint(0, grid_size - 1))
    grid[special_pos[0]][special_pos[1]] = special

    # Affichage de la grille dans l'embed
    grid_display = "\n".join(" ".join(row) for row in grid)
    embed.clear_fields()
    embed.add_field(name="🧊 Ombre", value=f"Trouve le carré **le plus {mode}** !", inline=False)
    embed.add_field(name="Grille :", value=grid_display, inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(prep_time)

    # Création des boutons (4x4)
    class GridView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=TIMEOUT)
            self.correct = False

    view = GridView()
    for i in range(grid_size):
        for j in range(grid_size):
            emoji = grid[i][j]
            async def make_callback(x=i, y=j):
                async def callback(interaction: discord.Interaction):
                    if interaction.user.id != get_user_id():
                        await interaction.response.send_message("🚫 Pas ton tour.", ephemeral=True)
                        return
                    view.correct = (x, y) == special_pos
                    view.stop()
                    await interaction.response.defer()
                return callback
            button = discord.ui.Button(label=emoji, style=discord.ButtonStyle.secondary)
            button.callback = await make_callback()
            view.add_item(button)

    await ctx.edit(embed=embed, view=view)
    await view.wait()
    return getattr(view, "correct", False)

ombre.title = "Ombre"
ombre.emoji = "🧊"
ombre.prep_time = 2

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🔤 Pagaille
# ────────────────────────────────────────────────────────────────────────────────
async def pagaille(ctx, embed, get_user_id, bot):
    prep_time = 2
    mot = random.choice(["amour", "cerveau", "maison", "voiture", "banane"])
    melange = "".join(random.sample(mot, len(mot)))

    embed.clear_fields()
    embed.add_field(name="🔤 Pagaille", value=f"{melange}\n➡️ Remets les lettres dans l’ordre !", inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(prep_time)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return msg.content.lower() == mot
    except:
        return False

pagaille.title = "Pagaille"
pagaille.emoji = "🔤"
pagaille.prep_time = 2

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ⚖️ Pair ou impair
# ────────────────────────────────────────────────────────────────────────────────
async def pair_ou_impair(ctx, embed, get_user_id, bot):
    prep_time = 1.5
    nombre = random.randint(10, 99)

    embed.clear_fields()
    embed.add_field(
        name="⚖️ Pair ou impair",
        value=f"Le nombre est **{nombre}**.\n➡️ Tape `pair` ou `impair` !",
        inline=False
    )
    await ctx.edit(embed=embed)
    await asyncio.sleep(prep_time)

    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        reponse = msg.content.lower().strip()
        if reponse not in ["pair", "impair"]:
            return False
        return (nombre % 2 == 0 and reponse == "pair") or (nombre % 2 == 1 and reponse == "impair")
    except:
        return False

pair_ou_impair.title = "Pair ou impair"
pair_ou_impair.emoji = "⚖️"
pair_ou_impair.prep_time = 1.5

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ⚡ Rapidité
# ────────────────────────────────────────────────────────────────────────────────
async def rapidite(ctx, embed, get_user_id, bot):
    prep_time = 2
    nums = random.sample(range(10, 99), 5)
    mode = random.choice(["grand", "petit"])
    embed.clear_fields()
    embed.add_field(name="⚡ Rapidité", value=f"Trouve le plus {mode} : {', '.join(map(str, nums))}", inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(prep_time)

    correct = max(nums) if mode == "grand" else min(nums)
    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == correct
    except:
        return False

rapidite.title = "Rapidité"
rapidite.emoji = "⚡"
rapidite.prep_time = 2

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ⚡ Réflexe couleur
# ────────────────────────────────────────────────────────────────────────────────
async def reflexe_couleur(ctx, embed, get_user_id, bot):
    prep_time = 2
    embed.clear_fields()
    embed.add_field(
        name="⚡ Réflexe couleur",
        value="Appuie sur le bouton **dès qu'il devient vert**.\nMais pas avant 👀",
        inline=False
    )
    await ctx.edit(embed=embed)
    await asyncio.sleep(prep_time)

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

    await asyncio.sleep(random.uniform(2, 5))
    if view.is_finished():
        return False

    button = view.children[0]
    button.label = "🟢 CLIQUE !"
    button.style = discord.ButtonStyle.success
    await msg.edit(view=view)
    view.start_time = asyncio.get_event_loop().time()
    await view.wait()

    if view.too_early or not view.clicked or view.reaction_time is None:
        return False
    return view.reaction_time < 1.2

reflexe_couleur.title = "Réflexe couleur"
reflexe_couleur.emoji = "🟢"
reflexe_couleur.prep_time = 2

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧩 Séquence de symboles
# ────────────────────────────────────────────────────────────────────────────────
async def sequence_symboles(ctx, embed, get_user_id, bot):
    symbols = ["⭐", "🍎", "🐍", "⚡", "🎲", "🍀", "🐱", "🔥"]
    seq = random.sample(symbols, 4)

    embed.clear_fields()
    embed.add_field(name="🧩 Séquence de symboles", value="Observe bien la séquence suivante :", inline=False)
    embed.add_field(name="Séquence :", value=" ".join(seq), inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(4)  # prep_time

    # On cache la séquence
    embed.clear_fields()
    question_type = random.choice(["position", "complete"])

    if question_type == "position":
        index = random.randint(0, len(seq) - 1)
        embed.add_field(name="🧩 Séquence de symboles", value=f"Quel était le **{index+1}ᵉ** emoji ?", inline=False)
        correct_answer = seq[index]
    else:
        embed.add_field(name="🧩 Séquence de symboles", value="Réécris la séquence complète !", inline=False)
        correct_answer = "".join(seq)

    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        user_input = msg.content.replace(" ", "")
        return user_input == correct_answer or user_input == "".join(correct_answer)
    except:
        return False

sequence_symboles.title = "Séquence de symboles"
sequence_symboles.emoji = "🧩"
sequence_symboles.prep_time = 4

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧩 Suite alphabétique
# ────────────────────────────────────────────────────────────────────────────────
async def suite_alpha(ctx, embed, get_user_id, bot):
    prep_time = 1
    sens_normal = random.choice([True, False])

    if sens_normal:
        start = random.randint(65, 70)
        step = random.randint(1, 3)
        serie = [chr(start + i * step) for i in range(4)]
        answer = chr(start + 4 * step)
    else:
        start = random.randint(85, 90)
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
    await asyncio.sleep(prep_time)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return msg.content.strip().upper() == answer
    except:
        return False

suite_alpha.title = "Suite alphabétique"
suite_alpha.emoji = "🧩"
suite_alpha.prep_time = 1

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ➗ Suite logique
# ────────────────────────────────────────────────────────────────────────────────
async def suite_logique(ctx, embed, get_user_id, bot):
    prep_time = 2
    type_suite = random.choice(["arithmétique", "géométrique", "alternée", "carrés", "fibonacci"])
    serie = []

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
            serie.append(serie[-1] + add if i % 2 == 1 else serie[-1] - sub)
    elif type_suite == "carrés":
        start = random.randint(1, 5)
        serie = [i ** 2 for i in range(start, start + 5)]
    elif type_suite == "fibonacci":
        a, b = random.randint(1, 5), random.randint(1, 5)
        serie = [a, b]
        for _ in range(3):
            serie.append(serie[-1] + serie[-2])

    answer_index = random.randint(0, 4)
    answer = serie[answer_index]
    display_serie = serie.copy()
    display_serie[answer_index] = "?"

    embed.clear_fields()
    embed.add_field(name="➗ Suite logique", value=f"{display_serie} ... ?", inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(prep_time)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == answer
    except:
        return False

suite_logique.title = "Suite logique"
suite_logique.emoji = "➗"
suite_logique.prep_time = 2

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🔎 Trouver la différence
# ────────────────────────────────────────────────────────────────────────────────
async def trouver_difference(ctx, embed, get_user_id, bot):
    prep_time = 1
    liste1 = [random.randint(1, 9) for _ in range(6)]
    liste2 = liste1.copy()
    diff_index = random.randint(0, 5)
    liste2[diff_index] = random.randint(1, 9)
    while liste2[diff_index] == liste1[diff_index]:
        liste2[diff_index] = random.randint(1, 9)

    embed.clear_fields()
    embed.add_field(name="🔎 Trouver la différence", value=f"{liste1} vs {liste2}", inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(prep_time)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == diff_index + 1
    except:
        return False

trouver_difference.title = "Trouver la différence"
trouver_difference.emoji = "🔎"
trouver_difference.prep_time = 1

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ✏️ Typographie erreur
# ────────────────────────────────────────────────────────────────────────────────
async def typo_trap(ctx, embed, get_user_id, bot):
    prep_time = 2  # Temps pour observer le mot avant de répondre

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
    await asyncio.sleep(prep_time)  # temps d'observation

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
typo_trap.prep_time = 2


#the end
