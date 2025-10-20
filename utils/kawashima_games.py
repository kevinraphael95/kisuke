# ────────────────────────────────────────────────────────────────────────────────
# 📌 kawashima_games.py — Mini-jeux Professeur Kawashima
# Objectif : Contient tous les mini-jeux cérébraux détectés automatiquement
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import random
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Paramètres
# ────────────────────────────────────────────────────────────────────────────────
TIMEOUT = 60  # 1 minute pour répondre à chaque mini-jeu

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Mini-jeux (chacun avec .emoji et .title)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧮 Addition cachée
# ────────────────────────────────────────────────────────────────────────────────
async def addition_cachee(ctx, embed, get_user_id, bot):
    additions = [random.randint(-9, 9) for _ in range(6)]
    total = sum(additions)

    embed.clear_fields()
    embed.add_field(name="🧮 Addition cachée", value="Observe bien les additions successives...", inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(2)

    for add in additions:
        embed.clear_fields()
        embed.add_field(name="🧮 Addition cachée", value=f"{add:+d}", inline=False)
        await ctx.edit(embed=embed)
        await asyncio.sleep(1.2)

    embed.clear_fields()
    embed.add_field(name="🧮 Addition cachée", value="Quel est le total final ?", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == total
    except:
        return False
addition_cachee.title = "Addition cachée"
addition_cachee.emoji = "➕"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧠 Calcul 2
# ────────────────────────────────────────────────────────────────────────────────
async def calcul_100(ctx, embed, get_user_id, bot):
    score = 0
    for _ in range(2):  # 5 calculs au lieu de 100 pour Discord (éviter la lourdeur)
        a, b = random.randint(1, 50), random.randint(1, 50)
        op = random.choice(["+", "-", "*", "/"])
        if op == "/":
            a = a * b
        question = f"{a} {op} {b} = ?"
        answer = int(eval(f"{a}{op}{b}"))

        embed.clear_fields()
        embed.add_field(name="🧠 Calcul 100", value=question, inline=False)
        await ctx.edit(embed=embed)

        try:
            msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
            if int(msg.content) == answer:
                score += 1
        except:
            break
    return score == 2
calcul_100.title = "Calcul 100"
calcul_100.emoji = "🧠"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧮 Calcul rapide
# ────────────────────────────────────────────────────────────────────────────────
async def calcul_rapide(ctx, embed, get_user_id, bot):
    a = random.randint(20, 80)
    b = random.randint(20, 80)
    op = random.choice(["+", "-", "*"])
    question = f"{a} {op} {b} = ?"
    answer = eval(f"{a}{op}{b}")

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
# 🔹 🎨 Couleurs (Stroop avec boutons réels)
# ────────────────────────────────────────────────────────────────────────────────
async def couleurs(ctx, bot):
    # Couleurs possibles sur Discord
    styles = {
        "bleu": discord.ButtonStyle.primary,
        "vert": discord.ButtonStyle.success,
        "rouge": discord.ButtonStyle.danger,
        "gris": discord.ButtonStyle.secondary
    }

    # Choix aléatoire du mot et de la couleur du bouton
    mot = random.choice(list(styles.keys())).upper()
    couleur_vraie = random.choice(list(styles.keys()))

    # Choix aléatoire de la question : mot ou couleur
    question_type = random.choice(["mot", "couleur"])
    if question_type == "mot":
        question_text = "Quel **MOT** est écrit sur le bouton ?"
        bonne_reponse = mot.lower()
    else:
        question_text = "Quelle est la **COULEUR** du bouton ?"
        bonne_reponse = couleur_vraie

    # Création du bouton
    button = Button(label=mot, style=styles[couleur_vraie])
    view = View()
    view.add_item(button)

    # Création de l'embed
    embed = discord.Embed(
        title="🎨 Couleurs (Stroop)",
        description=f"Regarde le bouton ci-dessous :\n➡️ {question_text}"
    )

    # Envoi du message avec embed + bouton
    await ctx.send(embed=embed, view=view)

    # Attente de la réponse texte
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == ctx.author.id,
            timeout=60  # tu peux remplacer par TIMEOUT
        )
        return msg.content.lower().strip() == bonne_reponse
    except:
        return False

# Ajout de métadonnées pour ton système
couleurs.title = "Couleurs"
couleurs.emoji = "🎨"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 📅 Datation
# ────────────────────────────────────────────────────────────────────────────────
async def datation(ctx, embed, get_user_id, bot):
    import datetime
    import calendar
    year = random.randint(2020, 2030)
    month = random.randint(1, 12)
    day = random.randint(1, calendar.monthrange(year, month)[1])
    date = datetime.date(year, month, day)
    jour = date.strftime("%A").lower()

    embed.clear_fields()
    embed.add_field(name="📅 Datation", value=f"Quel jour de la semaine était le {day}/{month}/{year} ?", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return msg.content.lower().startswith(jour[:3])  # permet "lun", "lundi", etc.
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
# 🔹 👁️ Mémoire visuelle
# ────────────────────────────────────────────────────────────────────────────────
async def memoire_visuelle(ctx, embed, get_user_id, bot):
    emojis = random.sample(["🍎", "🚗", "🐶", "🌟", "⚽", "🎲", "💎", "🎵"], 5)
    embed.clear_fields()
    embed.add_field(name="👁️ Mémoire visuelle", value=" ".join(emojis), inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(5)

    missing = random.choice(emojis)
    shown = [e for e in emojis if e != missing]
    embed.clear_fields()
    embed.add_field(name="👁️ Mémoire visuelle", value=f"Qu’est-ce qui manque ?\n{' '.join(shown)}", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return msg.content.strip() == missing
    except:
        return False
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
# 🔹 🧩 Suite alphabétique
# ────────────────────────────────────────────────────────────────────────────────
async def suite_alpha(ctx, embed, get_user_id, bot):
    start = random.randint(65, 70)
    step = random.randint(1, 3)
    serie = [chr(start + i * step) for i in range(4)]
    answer = chr(start + 4 * step)

    embed.clear_fields()
    embed.add_field(name="🧩 Suite alphabétique", value=f"{', '.join(serie)} ... ?", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return msg.content.upper() == answer
    except:
        return False
suite_alpha.title = "Suite alphabétique"
suite_alpha.emoji = "🧩"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ➗ Suite logique (version enrichie)
# ────────────────────────────────────────────────────────────────────────────────
async def suite_logique(ctx, embed, get_user_id, bot):
    type_suite = random.choice(["arithmétique", "géométrique", "alternée", "carrés", "fibonacci"])
    question = ""
    answer = None

    if type_suite == "arithmétique":
        start = random.randint(1, 10)
        step = random.randint(2, 6)
        serie = [start + i * step for i in range(4)]
        answer = serie[-1] + step
        question = f"{serie} ... ?"

    elif type_suite == "géométrique":
        start = random.randint(1, 5)
        ratio = random.randint(2, 3)
        serie = [start * (ratio ** i) for i in range(4)]
        answer = serie[-1] * ratio
        question = f"{serie} ... ?"

    elif type_suite == "alternée":
        start = random.randint(1, 10)
        add, sub = random.randint(2, 5), random.randint(1, 4)
        serie = [start]
        for i in range(1, 4):
            if i % 2 == 1:
                serie.append(serie[-1] + add)
            else:
                serie.append(serie[-1] - sub)
        answer = serie[-1] + (add if len(serie) % 2 == 1 else -sub)
        question = f"{serie} ... ?"

    elif type_suite == "carrés":
        start = random.randint(1, 5)
        serie = [i ** 2 for i in range(start, start + 4)]
        answer = (start + 4) ** 2
        question = f"{serie} ... ?"

    elif type_suite == "fibonacci":
        a, b = random.randint(1, 5), random.randint(1, 5)
        serie = [a, b]
        for _ in range(2, 4):
            serie.append(serie[-1] + serie[-2])
        answer = serie[-1] + serie[-2]
        question = f"{serie} ... ?"

    # Affichage
    embed.clear_fields()
    embed.add_field(name="➗ Suite logique", value=question, inline=False)
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
# 🔹 ✏️ Typo trap
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
        name="✏️ Typo trap",
        value=f"{mot_mod}\n➡️ Quelle lettre est fausse ? (ex: 'x')",
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

typo_trap.title = "Typo trap"
typo_trap.emoji = "✏️"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🚪 Va-et-vient
# ────────────────────────────────────────────────────────────────────────────────
async def va_et_vient(ctx, embed, get_user_id, bot):
    inside = 0
    for _ in range(5):
        action = random.choice(["entrent", "sortent"])
        n = random.randint(1, 4)
        if action == "entrent":
            inside += n
        else:
            inside = max(0, inside - n)

        phrase = f"{n} personnes {action} dans la maison."
        embed.clear_fields()
        embed.add_field(name="🚪 Va-et-vient", value=phrase, inline=False)
        await ctx.edit(embed=embed)
        await asyncio.sleep(1.5)

    embed.clear_fields()
    embed.add_field(name="🚪 Va-et-vient", value="Combien de personnes restent dans la maison ?", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == inside
    except:
        return False
va_et_vient.title = "Va-et-vient"
va_et_vient.emoji = "🚪"

