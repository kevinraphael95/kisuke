# ────────────────────────────────────────────────────────────────────────────────
# 📌 kawashima_games.py — Mini-jeux Professeur Kawashima
# Objectif : Contient tous les mini-jeux cérébraux détectés automatiquement
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import random
import asyncio
import datetime
import calendar

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Paramètres
# ────────────────────────────────────────────────────────────────────────────────
TIMEOUT = 60  # 1 minute pour répondre à chaque mini-jeu

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Fonction utilitaire — attendre une réponse commençant par "!"
# ────────────────────────────────────────────────────────────────────────────────
async def wait_for_prefixed_answer(bot, channel, user_id, timeout=TIMEOUT):
    """Attend une réponse commençant par ! et supprime le message après réception."""
    def check(msg):
        return msg.author.id == user_id and msg.channel == channel and msg.content.startswith("!")

    try:
        msg = await bot.wait_for("message", check=check, timeout=timeout)
        content = msg.content[1:].strip()
        await msg.delete(delay=0.5)
        return content
    except asyncio.TimeoutError:
        return None


# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧮 Calcul rapide
# ────────────────────────────────────────────────────────────────────────────────
async def calcul_rapide(ctx, embed, get_user_id, bot):
    a, b = random.randint(20, 80), random.randint(20, 80)
    op = random.choice(["+", "-", "*"])
    question = f"{a} {op} {b} = ?"
    answer = eval(f"{a}{op}{b}")

    embed.clear_fields()
    embed.add_field(name="🧮 Calcul rapide", value=question, inline=False)
    await ctx.edit(embed=embed)

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    if msg is None:
        return False
    try:
        return int(msg) == answer
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
    embed.add_field(name="🔢 Mémoire numérique", value="🕵️‍♂️ Retape la séquence (avec !) :", inline=False)
    await ctx.edit(embed=embed)

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    return msg == "".join(map(str, sequence)) if msg else False
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

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    return msg.lower() == intrus if msg else False
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
    embed.add_field(name="🔎 Trouver la différence", value=f"{liste2}\n➡️ Quelle position diffère (1-5) ?", inline=False)
    await ctx.edit(embed=embed)

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    try:
        return int(msg) == index + 1 if msg else False
    except:
        return False
trouver_difference.title = "Trouver la différence"
trouver_difference.emoji = "🔎"


# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ➗ Suite logique
# ────────────────────────────────────────────────────────────────────────────────
async def suite_logique(ctx, embed, get_user_id, bot):
    start, step = random.randint(1, 5), random.randint(2, 7)
    serie = [start + i * step for i in range(4)]
    answer = serie[-1] + step

    embed.clear_fields()
    embed.add_field(name="➗ Suite logique", value=f"{serie} ... ?", inline=False)
    await ctx.edit(embed=embed)

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    try:
        return int(msg) == answer if msg else False
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
    embed.add_field(name="✏️ Typo trap", value=f"{mot_mod}\n➡️ Quelle lettre est fausse ? (1-{len(mot)})", inline=False)
    await ctx.edit(embed=embed)

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    try:
        return int(msg) == typo_index + 1 if msg else False
    except:
        return False
typo_trap.title = "Typo trap"
typo_trap.emoji = "✏️"


# ────────────────────────────────────────────────────────────────────────────────
# 🔹 🧠 Calcul 100
# ────────────────────────────────────────────────────────────────────────────────
async def calcul_100(ctx, embed, get_user_id, bot):
    score = 0
    for _ in range(5):
        a, b = random.randint(1, 50), random.randint(1, 50)
        op = random.choice(["+", "-", "*", "/"])
        if op == "/":
            a = a * b
        question = f"{a} {op} {b} = ?"
        answer = int(eval(f"{a}{op}{b}"))

        embed.clear_fields()
        embed.add_field(name="🧠 Calcul 100", value=question, inline=False)
        await ctx.edit(embed=embed)

        msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
        try:
            if msg and int(msg) == answer:
                score += 1
        except:
            break
    return score >= 4
calcul_100.title = "Calcul 100"
calcul_100.emoji = "🧠"


# ────────────────────────────────────────────────────────────────────────────────
# 🔹 ➕ Addition cachée
# ────────────────────────────────────────────────────────────────────────────────
async def addition_cachee(ctx, embed, get_user_id, bot):
    additions = [random.randint(-9, 9) for _ in range(6)]
    total = sum(additions)

    embed.clear_fields()
    embed.add_field(name="➕ Addition cachée", value="Observe bien les additions successives...", inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(2)

    for add in additions:
        embed.clear_fields()
        embed.add_field(name="➕ Addition cachée", value=f"{add:+d}", inline=False)
        await ctx.edit(embed=embed)
        await asyncio.sleep(1.2)

    embed.clear_fields()
    embed.add_field(name="➕ Addition cachée", value="➡️ Quel est le total final ?", inline=False)
    await ctx.edit(embed=embed)

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    try:
        return int(msg) == total if msg else False
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
        inside = inside + n if action == "entrent" else max(0, inside - n)

        embed.clear_fields()
        embed.add_field(name="🚪 Va-et-vient", value=f"{n} personnes {action} dans la maison.", inline=False)
        await ctx.edit(embed=embed)
        await asyncio.sleep(1.5)

    embed.clear_fields()
    embed.add_field(name="🚪 Va-et-vient", value="➡️ Combien de personnes restent dans la maison ?", inline=False)
    await ctx.edit(embed=embed)

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    try:
        return int(msg) == inside if msg else False
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

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    try:
        user_hours, user_mins = map(int, msg.replace('h', ' ').replace(':', ' ').split())
        return user_hours == hours and user_mins == mins if msg else False
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
    embed.add_field(name="🔤 Pagaille", value=f"{melange}\n➡️ Remets les lettres dans l’ordre (avec !)", inline=False)
    await ctx.edit(embed=embed)

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    return msg.lower() == mot if msg else False
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
    embed.add_field(
        name="🎨 Couleurs",
        value=f"Mot : **{mot}** (affiché en {couleur_vraie.upper()})\n➡️ Quelle est la **COULEUR** des lettres ? (avec !)",
        inline=False
    )
    await ctx.edit(embed=embed)

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    return msg.lower() == couleur_vraie if msg else False
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
    embed.add_field(name="💰 Monnaie", value=f"Prix : {prix:.2f} €\nPayé : {donne:.2f} €\n➡️ Quelle monnaie rends-tu ? (avec !)", inline=False)
    await ctx.edit(embed=embed)

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    try:
        return abs(float(msg.replace(",", ".").strip()) - rendu) < 0.01 if msg else False
    except:
        return False
monnaie.title = "Monnaie"
monnaie.emoji = "💰"


# ────────────────────────────────────────────────────────────────────────────────
# 🔹 📅 Datation
# ────────────────────────────────────────────────────────────────────────────────
async def datation(ctx, embed, get_user_id, bot):
    year, month = random.randint(2020, 2030), random.randint(1, 12)
    day = random.randint(1, calendar.monthrange(year, month)[1])
    date = datetime.date(year, month, day)
    jour = date.strftime("%A").lower()

    embed.clear_fields()
    embed.add_field(name="📅 Datation", value=f"➡️ Quel jour de la semaine était le {day}/{month}/{year} ? (avec !)", inline=False)
    await ctx.edit(embed=embed)

    msg = await wait_for_prefixed_answer(bot, ctx.channel, get_user_id())
    return msg.lower().startswith(jour[:3]) if msg else False
datation.title = "Datation"
datation.emoji = "📅"
