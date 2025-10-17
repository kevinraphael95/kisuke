# ────────────────────────────────────────────────────────────────────────────────
# 📌 cook.py — Mini-jeu Cooking Mama avec boutons et mini-jeux variés
# Objectif : Préparer une recette façon Cooking Mama avec mini-jeux interactifs
# Catégorie : Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Select
import json
import random
import asyncio
from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Cooking(commands.Cog):
    """
    Commande /cook et !cook — Mini-jeu Cooking Mama avec boutons et mini-jeux
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.recipes_path = Path("data/recipes.json")
        self.minigames_path = Path("data/minigames.json")
        self.recipes = self.load_json(self.recipes_path)
        self.minigames = self.load_json(self.minigames_path)

    # ────────────────────────────────────────────────────────────────────────────
    # 📂 Chargement JSON
    # ────────────────────────────────────────────────────────────────────────────
    def load_json(self, path: Path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="cook",
        description="Prépare une recette façon Cooking Mama !"
    )
    @app_commands.describe(recette="Nom de la recette à cuisiner")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_cook(self, interaction: discord.Interaction, recette: str = None):
        """Commande slash : /cook <recette>"""
        await self.run_cooking_game(interaction, recette, is_slash=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="cook")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_cook(self, ctx: commands.Context, recette: str = None):
        """Commande préfixe : !cook <recette>"""
        await self.run_cooking_game(ctx, recette, is_slash=False)

    # ────────────────────────────────────────────────────────────────────────────
    # 🍳 Logique principale du mini-jeu
    # ────────────────────────────────────────────────────────────────────────────
    async def run_cooking_game(self, origin, recette: str, is_slash: bool):
        send = origin.response.send_message if is_slash else origin.send
        channel = origin.channel if not is_slash else origin.channel
        user = origin.user if is_slash else origin.author
        mention = user.mention

        # Vérification recette
        if not recette or recette.lower() not in self.recipes:
            names = ", ".join(self.recipes.keys())
            return await send(f"Choisis une recette : {names}", ephemeral=is_slash)

        recipe = self.recipes[recette.lower()]
        steps = recipe["etapes"]
        score = 0

        await send(f"👩‍🍳 {mention} commence à cuisiner **{recipe['nom']}** !")

        for step in steps:
            mg_type = step["type"]
            mg_config = self.minigames.get(mg_type)
            if not mg_config:
                await channel.send(f"⚠️ Mini-jeu {mg_type} non trouvé, on saute cette étape.")
                continue

            await self.run_minigame(user, channel, step, mg_config)
            score += 1  # simple incrément, on peut ajouter réussite/échec plus tard

        # Résultat final
        if score == len(steps):
            result = f"🎉 Bravo {mention} ! Ton **{recipe['nom']}** est parfait ! 🍽️"
        elif score >= len(steps) / 2:
            result = f"😋 Ton **{recipe['nom']}** est bon, mais pas parfait."
        else:
            result = f"💀 Oups… ton **{recipe['nom']}** est raté !"

        await channel.send(result)

    # ────────────────────────────────────────────────────────────────────────────
    # 🎮 Exécution d’un mini-jeu selon type
    # ────────────────────────────────────────────────────────────────────────────
    async def run_minigame(self, user, channel, step, mg_config):
        mg_type = mg_config["type"]

        if mg_type == "reaction":
            await self.minigame_reflexe(user, channel, step, mg_config)
        elif mg_type == "timing":
            await self.minigame_timing(user, channel, step, mg_config)
        elif mg_type == "memory":
            await self.minigame_memoire(user, channel, step, mg_config)
        elif mg_type == "buttons":
            await self.minigame_buttons(user, channel, step, mg_config)
        elif mg_type == "grid":
            await self.minigame_dressage(user, channel, step, mg_config)
        elif mg_type == "spam":
            await self.minigame_mixage(user, channel, step, mg_config)
        elif mg_type == "quiz":
            await self.minigame_quiz(user, channel, step, mg_config)
        else:
            await channel.send(f"⚠️ Mini-jeu `{mg_type}` non implémenté.")

    # ────────────────────────────────────────────────────────────────────────────
    # Mini-jeux
    # ────────────────────────────────────────────────────────────────────────────

    async def minigame_reflexe(self, user, channel, step, mg_config):
        msg = await channel.send(f"**{step['nom']}** — {step['emoji']} | Clique vite !")
        await msg.add_reaction(step["emoji"])

        def check(reaction, u):
            return u == user and str(reaction.emoji) == step["emoji"] and reaction.message.id == msg.id

        try:
            await self.bot.wait_for("reaction_add", timeout=mg_config.get("temps", 3), check=check)
            await channel.send("✅ Bien joué !")
        except asyncio.TimeoutError:
            await channel.send("❌ Trop lent !")

    async def minigame_buttons(self, user, channel, step, mg_config):
        # On crée plusieurs boutons, un seul correct
        correct = step["emoji"]
        emojis = [correct] + ["🍎", "🍌", "🥦", "🍅", "🧄"]
        random.shuffle(emojis)
        buttons = [Button(label=e, style=discord.ButtonStyle.primary) for e in emojis[:mg_config.get("nb_items", 4)]]

        view = View(timeout=5)
        result = {"done": False}

        for b in buttons:
            async def callback(interaction, b=b):
                if interaction.user != user:
                    return await interaction.response.send_message("⛔ Ce n'est pas ton tour !", ephemeral=True)
                if b.label == correct:
                    await interaction.response.send_message("✅ Correct !", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Mauvais !", ephemeral=True)
                result["done"] = True
                view.stop()
            b.callback = callback
            view.add_item(b)

        await channel.send(f"**{step['nom']}** — Choisis le bon ingrédient !", view=view)
        await view.wait()
        if not result["done"]:
            await channel.send("⏱️ Temps écoulé !")

    # Pour simplifier, les autres mini-jeux (timing, mémoire, dressage, mixage, quiz)
    # peuvent être ajoutés de la même manière avec buttons, embeds, messages
    async def minigame_timing(self, user, channel, step, mg_config):
        await channel.send(f"**{step['nom']}** — Timing ! Clique quand la barre est verte (simulé). ⏱️")
        await asyncio.sleep(1)
        await channel.send("✅ Étape terminée ! (simulation)")

    async def minigame_memoire(self, user, channel, step, mg_config):
        await channel.send(f"**{step['nom']}** — Mémoire ! Retenir la séquence... (simulé)")
        await asyncio.sleep(1)
        await channel.send("✅ Étape terminée ! (simulation)")

    async def minigame_dressage(self, user, channel, step, mg_config):
        await channel.send(f"**{step['nom']}** — Dressage artistique ! (simulé)")
        await asyncio.sleep(1)
        await channel.send("✅ Étape terminée ! (simulation)")

    async def minigame_mixage(self, user, channel, step, mg_config):
        await channel.send(f"**{step['nom']}** — Mixage équilibré ! (simulé)")
        await asyncio.sleep(1)
        await channel.send("✅ Étape terminée ! (simulation)")

    async def minigame_quiz(self, user, channel, step, mg_config):
        question = random.choice(mg_config.get("questions", []))
        options = question["options"]
        view = View(timeout=10)
        result = {"done": False}

        for opt in options:
            btn = Button(label=opt, style=discord.ButtonStyle.primary)
            async def callback(interaction, opt=opt):
                if interaction.user != user:
                    return await interaction.response.send_message("⛔ Ce n'est pas ton tour !", ephemeral=True)
                if opt == question["bonne"]:
                    await interaction.response.send_message("✅ Correct !", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ Mauvais ! La bonne réponse était {question['bonne']}", ephemeral=True)
                result["done"] = True
                view.stop()
            btn.callback = callback
            view.add_item(btn)

        await channel.send(f"**{step['nom']}** — {question['q']}", view=view)
        await view.wait()
        if not result["done"]:
            await channel.send("⏱️ Temps écoulé !")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Cooking(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
