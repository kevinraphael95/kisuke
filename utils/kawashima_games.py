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
