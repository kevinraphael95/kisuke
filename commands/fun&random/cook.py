# ────────────────────────────────────────────────────────────────────────────────
# 📌 cook.py — Commande simple /cook et !cook
# Objectif : Lancer un mini-jeu de cuisine inspiré de Cooking Mama
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
import json
import random
import asyncio
from pathlib import Path

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Cooking(commands.Cog):
    """
    Commande /cook et !cook — Joue à un mini-jeu de cuisine inspiré de Cooking Mama
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data_path = Path("data/recipes.json")

    # ────────────────────────────────────────────────────────────────────────────
    # 📂 Chargement des recettes
    # ────────────────────────────────────────────────────────────────────────────
    def load_recipes(self):
        with open(self.data_path, "r", encoding="utf-8") as f:
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
    # 🍳 Logique du mini-jeu
    # ────────────────────────────────────────────────────────────────────────────
    async def run_cooking_game(self, origin, recette: str, is_slash: bool):
        recipes = self.load_recipes()
        names = list(recipes.keys())

        if not recette or recette.lower() not in recipes:
            txt = f"Choisis une recette : {', '.join(names)}"
            if is_slash:
                return await origin.response.send_message(txt, ephemeral=True)
            else:
                return await origin.send(txt)

        recipe = recipes[recette.lower()]
        steps = recipe["etapes"]
        score = 0

        mention = origin.user.mention if is_slash else origin.author.mention
        send = origin.response.send_message if is_slash else origin.send

        await send(f"👩‍🍳 {mention} commence à cuisiner **{recipe['nom']}** !")

        for step in steps:
            message = await (origin.channel.send if is_slash else origin.send)(f"**{step['nom']}** — {step['action']}")
            emoji = step["emoji"]
            await message.add_reaction(emoji)

            def check(reaction, user):
                return user == (origin.user if is_slash else origin.author) and str(reaction.emoji) == emoji and reaction.message.id == message.id

            try:
                await self.bot.wait_for("reaction_add", timeout=step.get("delai", 4.0), check=check)
                await origin.channel.send("✅ Parfait !")
                score += 1
            except asyncio.TimeoutError:
                await origin.channel.send("❌ Trop lent !")

        # Résultat final
        if score == len(steps):
            result = f"🎉 Bravo {mention} ! Ton **{recipe['nom']}** est parfait ! 🍽️"
        elif score >= len(steps) / 2:
            result = f"😋 Ton **{recipe['nom']}** est bon, mais pas parfait."
        else:
            result = f"💀 Oups… ton **{recipe['nom']}** est raté !"

        await origin.channel.send(result)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Cooking(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun&Random"
    await bot.add_cog(cog)
