# ────────────────────────────────────────────────────────────────────────────────
# 📌 division.py — Commande interactive !division
# Objectif : Déterminer la division qui te correspond via un QCM à choix emoji
# Catégorie : VAACT
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
import json
import os
from collections import Counter
import asyncio

DATA_JSON_PATH = os.path.join("data", "division_traits.json")

def load_division_data():
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

class Division(commands.Cog):
    """
    Commande !division — Détermine ta division parmi les 13.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="division",
        help="Détermine ta division dans le Gotei 13.",
        description="Réponds à quelques questions pour savoir dans quelle division tu serais."
    )
    async def division(self, ctx: commands.Context):
        """Commande principale QCM de division."""
        try:
            data = load_division_data()
            questions = data["questions"]
            divisions = data["divisions"]
            personality_counter = Counter()

            def get_emoji(index):
                return ["🇦", "🇧", "🇨", "🇩"][index]

            for q in questions:
                desc = ""
                emojis = []
                for i, (answer, traits) in enumerate(q["answers"].items()):
                    emoji = get_emoji(i)
                    desc += f"{emoji} {answer}\n"
                    emojis.append((emoji, answer, traits))

                embed = discord.Embed(
                    title="🧠 Test de division",
                    description=f"**{q['question']}**\n\n{desc}",
                    color=discord.Color.orange()
                )
                message = await ctx.send(embed=embed)
                for emoji, _, _ in emojis:
                    await message.add_reaction(emoji)

                def check(reaction, user):
                    return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in [e[0] for e in emojis]

                try:
                    reaction, _ = await ctx.bot.wait_for("reaction_add", timeout=60.0, check=check)
                    selected_emoji = str(reaction.emoji)
                    selected_traits = next(traits for emoji, _, traits in emojis if emoji == selected_emoji)
                    personality_counter.update(selected_traits)
                except asyncio.TimeoutError:
                    await ctx.send("⏱️ Temps écoulé. Test annulé.")
                    return

            # Calculer la division correspondante
            division_scores = {
                div: sum(personality_counter[trait] for trait in traits)
                for div, traits in divisions.items()
            }
            best_division = max(division_scores, key=division_scores.get)

            embed_result = discord.Embed(
                title="🧩 Résultat de ton test",
                description=f"Tu serais dans la **{best_division}** !",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed_result)

        except Exception as e:
            print(f"[ERREUR division] {e}")
            await ctx.send("❌ Une erreur est survenue lors du test.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Division(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
