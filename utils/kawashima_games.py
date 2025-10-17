# ────────────────────────────────────────────────────────────────────────────────
# 📌 kawashima_games.py — Mini-jeux Professeur Kawashima
# Objectif : Contient tous les mini-jeux cérébraux
# ────────────────────────────────────────────────────────────────────────────────
import random
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Mini-jeux
# ────────────────────────────────────────────────────────────────────────────────
async def calcul_rapide(ctx, send, get_user_id, bot):
    a = random.randint(10, 50)
    b = random.randint(10, 50)
    op = random.choice(["+", "-", "*"])
    question = f"{a} {op} {b} = ?"
    answer = eval(f"{a}{op}{b}")
    await send(f"🧮 **Calcul rapide** : {question}")
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=12
        )
        if int(msg.content) == answer:
            await send("✅ Correct !")
        else:
            await send(f"❌ Faux ! La réponse était {answer}")
    except:
        await send(f"⏱ Temps écoulé ! La réponse était {answer}")

async def memoire_numerique(ctx, send, get_user_id, bot):
    sequence = [random.randint(0, 9) for _ in range(6)]
    await send(f"🔢 **Mémoire numérique** : {sequence}")
    await asyncio.sleep(6)  # temps pour retenir
    await send("🕵️‍♂️ La séquence a disparu, retapez-la !")
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=15
        )
        if msg.content == "".join(map(str, sequence)):
            await send("✅ Correct !")
        else:
            await send(f"❌ Faux ! C'était {''.join(map(str, sequence))}")
    except:
        await send(f"⏱ Temps écoulé ! La séquence était {''.join(map(str, sequence))}")

async def trouver_intrus(ctx, send, get_user_id, bot):
    mots = ["pomme", "banane", "orange", "voiture", "stylo", "livre"]
    intrus = random.choice(mots)
    shuffle = random.sample(mots, len(mots))
    await send(f"🔍 **Trouver l’intrus** : {shuffle}")
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=12
        )
        if msg.content.lower() == intrus:
            await send("✅ Correct !")
        else:
            await send(f"❌ Faux ! L’intrus était {intrus}")
    except:
        await send(f"⏱ Temps écoulé ! L’intrus était {intrus}")

async def trouver_difference(ctx, send, get_user_id, bot):
    liste1 = [random.randint(1, 9) for _ in range(5)]
    liste2 = liste1.copy()
    index = random.randint(0, 4)
    liste2[index] = random.randint(10, 20)
    await send(f"🔎 **Trouver la différence** : {liste2}")
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=12
        )
        if int(msg.content) == index + 1:
            await send("✅ Correct !")
        else:
            await send(f"❌ Faux ! La différence était à la position {index + 1}")
    except:
        await send(f"⏱ Temps écoulé ! La différence était à la position {index + 1}")

async def suite_logique(ctx, send, get_user_id, bot):
    start = random.randint(1, 5)
    step = random.randint(2, 7)
    serie = [start + i * step for i in range(4)]
    answer = serie[-1] + step
    await send(f"➗ **Suite logique** : {serie} ... ?")
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=12
        )
        if int(msg.content) == answer:
            await send("✅ Correct !")
        else:
            await send(f"❌ Faux ! La réponse était {answer}")
    except:
        await send(f"⏱ Temps écoulé ! La réponse était {answer}")

async def typo_trap(ctx, send, get_user_id, bot):
    mot = random.choice(["chien", "maison", "voiture", "ordinateur"])
    typo_index = random.randint(0, len(mot)-1)
    mot_mod = list(mot)
    mot_mod[typo_index] = chr(random.randint(97, 122))
    mot_mod = "".join(mot_mod)
    await send(f"✏️ **Typo trap** : {mot_mod}")
    try:
        msg = await bot.wait_for(
            "message",
            check=lambda m: m.author.id == get_user_id(),
            timeout=12
        )
        if int(msg.content) == typo_index + 1:
            await send("✅ Correct !")
        else:
            await send(f"❌ Faux ! L’erreur était à la position {typo_index + 1}")
    except:
        await send(f"⏱ Temps écoulé ! L’erreur était à la position {typo_index + 1}")
