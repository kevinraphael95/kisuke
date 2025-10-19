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
# 🔹 🔍 Trouver l’intrus
# ────────────────────────────────────────────────────────────────────────────────
async def trouver_intrus(ctx, embed, get_user_id, bot):
    mots = ["pomme", "banane", "orange", "voiture", "stylo", "livre"]
    intrus = random.choice(mots)
    affichage = random.sample(mots, len(mots))

    embed.clear_fields()
    embed.add_field(name="🔍 Trouver l’intrus", value=", ".join(affichage), inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return msg.content.lower() == intrus
    except:
        return False
trouver_intrus.title = "Trouver l’intrus"
trouver_intrus.emoji = "🔍"

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
# 🔹 ➗ Suite logique
# ────────────────────────────────────────────────────────────────────────────────
async def suite_logique(ctx, embed, get_user_id, bot):
    start = random.randint(1, 5)
    step = random.randint(2, 7)
    serie = [start + i * step for i in range(4)]
    answer = serie[-1] + step

    embed.clear_fields()
    embed.add_field(name="➗ Suite logique", value=f"{serie} ... ?", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == answer
    except:
        return False
suite_logique.title = "Suite logique"
suite_logique.emoji = "➗"

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ✏️ Typo trap
# ────────────────────────────────────────────────────────────────────────────────
async def typo_trap(ctx, embed, get_user_id, bot):
    mot = random.choice(["chien", "maison", "voiture", "ordinateur"])
    typo_index = random.randint(0, len(mot) - 1)
    mot_mod = list(mot)
    mot_mod[typo_index] = chr(random.randint(97, 122))
    mot_mod = "".join(mot_mod)

    embed.clear_fields()
    embed.add_field(name="✏️ Typo trap", value=f"{mot_mod}\nQuelle lettre est fausse ? (1-{len(mot)})", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return int(msg.content) == typo_index + 1
    except:
        return False
typo_trap.title = "Typo trap"
typo_trap.emoji = "✏️"


# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧠 Calcul 100
# ────────────────────────────────────────────────────────────────────────────────
async def calcul_100(ctx, embed, get_user_id, bot):
    score = 0
    for _ in range(5):  # 5 calculs au lieu de 100 pour Discord (éviter la lourdeur)
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
    return score >= 4
calcul_100.title = "Calcul 100"
calcul_100.emoji = "🧠"

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

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🕒 Heures
# ────────────────────────────────────────────────────────────────────────────────
async def heures(ctx, embed, get_user_id, bot):
    h1, m1 = random.randint(0, 23), random.randint(0, 59)
    h2, m2 = random.randint(0, 23), random.randint(0, 59)
    diff = abs((h1 * 60 + m1) - (h2 * 60 + m2))
    hours, mins = divmod(diff, 60)

    embed.clear_fields()
    embed.add_field(name="🕒 Heures", value=f"Différence entre {h1:02d}:{m1:02d} et {h2:02d}:{m2:02d} ?", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        user_hours, user_mins = map(int, msg.content.replace("h", " ").replace(":", " ").split())
        return user_hours == hours and user_mins == mins
    except:
        return False
heures.title = "Heures"
heures.emoji = "🕒"

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
# 🔹 🎨 Couleurs (effet Stroop)
# ────────────────────────────────────────────────────────────────────────────────
async def couleurs(ctx, embed, get_user_id, bot):
    mots = ["ROUGE", "BLEU", "JAUNE", "NOIR"]
    couleurs = ["rouge", "bleu", "jaune", "noir"]
    mot = random.choice(mots)
    couleur_vraie = random.choice(couleurs)

    embed.clear_fields()
    embed.add_field(name="🎨 Couleurs", value=f"Mot : **{mot}**\nCouleur du texte : (simulée) {couleur_vraie.upper()}\n➡️ Quelle est la COULEUR des lettres ?", inline=False)
    await ctx.edit(embed=embed)

    try:
        msg = await bot.wait_for("message", check=lambda m: m.author.id == get_user_id(), timeout=TIMEOUT)
        return msg.content.lower() == couleur_vraie
    except:
        return False
couleurs.title = "Couleurs"
couleurs.emoji = "🎨"

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
# 🔹 🔢 Carré magique 3x3 aléatoire emoji
# ────────────────────────────────────────────────────────────────────────────────
async def carre_magique_aleatoire_emoji(ctx, embed, get_user_id, bot):
    import itertools

    # Fonction pour vérifier si un carré est magique
    def is_magic(square):
        s = 15  # somme magique pour 3x3 avec 1..9
        rows = all(sum(row) == s for row in square)
        cols = all(sum(col) == s for col in zip(*square))
        diags = sum(square[i][i] for i in range(3)) == s and sum(square[i][2-i] for i in range(3)) == s
        return rows and cols and diags

    # Générer aléatoirement un carré magique 3x3
    nums = list(range(1, 10))
    for _ in range(1000):  # essayer 1000 permutations max
        random.shuffle(nums)
        square = [nums[0:3], nums[3:6], nums[6:9]]
        if is_magic(square):
            break

    # Cacher un nombre au hasard
    row, col = random.randint(0, 2), random.randint(0, 2)
    answer = square[row][col]
    square[row][col] = "?"

    # Conversion en emoji Discord
    num_to_emoji = {
        1: "1️⃣", 2: "2️⃣", 3: "3️⃣",
        4: "4️⃣", 5: "5️⃣", 6: "6️⃣",
        7: "7️⃣", 8: "8️⃣", 9: "9️⃣"
    }

    display = ""
    for r in square:
        display += " | ".join(num_to_emoji.get(x, x) for x in r) + "\n"

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

carre_magique_aleatoire_emoji.title = "Carré magique 3x3"
carre_magique_aleatoire_emoji.emoji = "🔢"

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
