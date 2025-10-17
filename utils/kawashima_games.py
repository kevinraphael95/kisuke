# ────────────────────────────────────────────────────────────────────────────────
# 📌 kawashima_games.py — Mini-jeux Professeur Kawashima
# Objectif : Contient tous les mini-jeux cérébraux
# ────────────────────────────────────────────────────────────────────────────────
import random
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Mini-jeux
# ────────────────────────────────────────────────────────────────────────────────
TIMEOUT = 60  # temps de réaction pour chaque mini-jeu en secondes

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
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return int(msg.content) == answer
    except:
        return False

async def memoire_numerique(ctx, embed, get_user_id, bot):
    sequence = [random.randint(0, 9) for _ in range(6)]
    embed.clear_fields()
    embed.add_field(name="🔢 Mémoire numérique", value=str(sequence), inline=False)
    await ctx.edit(embed=embed)
    await asyncio.sleep(5)
    embed.clear_fields()
    embed.add_field(name="🔢 Mémoire numérique", value="🕵️‍♂️ Séquence disparue, retapez-la !", inline=False)
    await ctx.edit(embed=embed)
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return msg.content == "".join(map(str, sequence))
    except:
        return False

async def trouver_intrus(ctx, embed, get_user_id, bot):
    mots = ["pomme", "banane", "orange", "voiture", "stylo", "livre"]
    intrus = random.choice(mots)
    shuffle = random.sample(mots, len(mots))
    embed.clear_fields()
    embed.add_field(name="🔍 Trouver l’intrus", value=str(shuffle), inline=False)
    await ctx.edit(embed=embed)
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return msg.content.lower() == intrus
    except:
        return False

async def trouver_difference(ctx, embed, get_user_id, bot):
    liste1 = [random.randint(1, 9) for _ in range(5)]
    liste2 = liste1.copy()
    index = random.randint(0, 4)
    liste2[index] = random.randint(10, 20)
    embed.clear_fields()
    embed.add_field(name="🔎 Trouver la différence", value=str(liste2), inline=False)
    await ctx.edit(embed=embed)
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return int(msg.content) == index + 1
    except:
        return False

async def suite_logique(ctx, embed, get_user_id, bot):
    start = random.randint(1, 5)
    step = random.randint(2, 7)
    serie = [start + i * step for i in range(4)]
    answer = serie[-1] + step
    embed.clear_fields()
    embed.add_field(name="➗ Suite logique", value=str(serie) + " ... ?", inline=False)
    await ctx.edit(embed=embed)
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return int(msg.content) == answer
    except:
        return False

async def typo_trap(ctx, embed, get_user_id, bot):
    mot = random.choice(["chien", "maison", "voiture", "ordinateur"])
    typo_index = random.randint(0, len(mot)-1)
    mot_mod = list(mot)
    mot_mod[typo_index] = chr(random.randint(97, 122))
    mot_mod = "".join(mot_mod)
    embed.clear_fields()
    embed.add_field(name="✏️ Typo trap", value=mot_mod, inline=False)
    await ctx.edit(embed=embed)
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=TIMEOUT
        )
        return int(msg.content) == typo_index + 1
    except:
        return False
