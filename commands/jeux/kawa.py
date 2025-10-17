# ────────────────────────────────────────────────────────────────────────────────
# 📌 kawashima.py — Commande /kawashima et !kawashima
# Objectif : Lancer tous les mini-jeux style Professeur Kawashima (entraînement cérébral)
# Catégorie : Autre
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Kawashima(commands.Cog):
    """
    Commande /kawashima et !kawashima — Mini-jeux style Professeur Kawashima
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.minijeux = [
            "calcul_rapide",
            "memoire_numerique",
            "trouver_intrus",
            "trouver_difference",
            "suite_logique",
            "typo_trap"
        ]

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="kawashima",
        description="Lance un mini-jeu d'entraînement cérébral !"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_kawashima(self, interaction: discord.Interaction):
        jeu = random.choice(self.minijeux)
        await interaction.response.send_message(f"🎮 Mini-jeu : **{jeu}**")
        await self.lancer_minijeu(interaction, jeu)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="kawashima", aliases=["k"], help="Lance un mini-jeu d'entraînement cérébral!")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_kawashima(self, ctx: commands.Context):
        jeu = random.choice(self.minijeux)
        await ctx.send(f"🎮 Mini-jeu : **{jeu}**")
        await self.lancer_minijeu(ctx, jeu)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction pour lancer chaque mini-jeu
    # ────────────────────────────────────────────────────────────────────────────
    async def lancer_minijeu(self, ctx_or_interaction, nom_jeu):
        def send(text):
            return ctx_or_interaction.followup.send(text) if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.send(text)

        def get_user_id():
            return ctx_or_interaction.user.id if isinstance(ctx_or_interaction, discord.Interaction) else ctx_or_interaction.author.id

        # ───── Calcul rapide ─────
        if nom_jeu == "calcul_rapide":
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            op = random.choice(["+", "-", "*"])
            question = f"{a} {op} {b} = ?"
            answer = eval(f"{a}{op}{b}")
            await send(f"🧮 **Calcul rapide** : {question}")
            try:
                msg = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == get_user_id(),
                    timeout=10
                )
                if int(msg.content) == answer:
                    await send("✅ Correct !")
                else:
                    await send(f"❌ Faux ! La réponse était {answer}")
            except asyncio.TimeoutError:
                await send(f"⏱ Temps écoulé ! La réponse était {answer}")

        # ───── Mémoire numérique ─────
        elif nom_jeu == "memoire_numerique":
            sequence = [random.randint(1, 9) for _ in range(5)]
            await send(f"🔢 **Mémoire numérique** : {sequence}")
            await asyncio.sleep(5)
            await send("Retapez la séquence !")
            try:
                msg = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == get_user_id(),
                    timeout=15
                )
                if msg.content == "".join(map(str, sequence)):
                    await send("✅ Correct !")
                else:
                    await send(f"❌ Faux ! La séquence était {''.join(map(str, sequence))}")
            except asyncio.TimeoutError:
                await send(f"⏱ Temps écoulé ! La séquence était {''.join(map(str, sequence))}")

        # ───── Trouver l’intrus ─────
        elif nom_jeu == "trouver_intrus":
            mots = ["pomme", "banane", "orange", "voiture"]
            intrus = random.choice(mots)
            shuffle = random.sample(mots, len(mots))
            await send(f"🔍 **Trouver l’intrus** : {shuffle}")
            try:
                msg = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == get_user_id(),
                    timeout=10
                )
                if msg.content.lower() == intrus:
                    await send("✅ Correct !")
                else:
                    await send(f"❌ Faux ! L’intrus était {intrus}")
            except asyncio.TimeoutError:
                await send(f"⏱ Temps écoulé ! L’intrus était {intrus}")

        # ───── Trouver la différence ─────
        elif nom_jeu == "trouver_difference":
            liste1 = [random.randint(1, 9) for _ in range(5)]
            liste2 = liste1.copy()
            index = random.randint(0, 4)
            liste2[index] = random.randint(10, 20)
            await send(f"🔎 **Trouver la différence** : {liste2}")
            try:
                msg = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == get_user_id(),
                    timeout=10
                )
                if int(msg.content) == index + 1:
                    await send("✅ Correct !")
                else:
                    await send(f"❌ Faux ! La différence était à la position {index + 1}")
            except asyncio.TimeoutError:
                await send(f"⏱ Temps écoulé ! La différence était à la position {index + 1}")

        # ───── Suite logique ─────
        elif nom_jeu == "suite_logique":
            start = random.randint(1, 5)
            step = random.randint(1, 5)
            serie = [start + i * step for i in range(4)]
            answer = serie[-1] + step
            await send(f"➗ **Suite logique** : {serie} ... ?")
            try:
                msg = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == get_user_id(),
                    timeout=10
                )
                if int(msg.content) == answer:
                    await send("✅ Correct !")
                else:
                    await send(f"❌ Faux ! La réponse était {answer}")
            except asyncio.TimeoutError:
                await send(f"⏱ Temps écoulé ! La réponse était {answer}")

        # ───── Typo trap ─────
        elif nom_jeu == "typo_trap":
            mot = random.choice(["chien", "maison", "voiture"])
            typo_index = random.randint(0, len(mot)-1)
            mot_mod = list(mot)
            mot_mod[typo_index] = chr(random.randint(97, 122))
            mot_mod = "".join(mot_mod)
            await send(f"✏️ **Typo trap** : {mot_mod}")
            try:
                msg = await self.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == get_user_id(),
                    timeout=10
                )
                if int(msg.content) == typo_index + 1:
                    await send("✅ Correct !")
                else:
                    await send(f"❌ Faux ! L’erreur était à la position {typo_index + 1}")
            except asyncio.TimeoutError:
                await send(f"⏱ Temps écoulé ! L’erreur était à la position {typo_index + 1}")

        else:
            await send("🔹 Ce mini-jeu n’est pas encore implémenté.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Kawashima(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Autre"
    await bot.add_cog(cog)
