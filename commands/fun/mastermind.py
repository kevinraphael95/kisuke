# ────────────────────────────────────────────────────────────────────────────────
# 📌 mastermind.py — Commande !mastermind
# Objectif : Deviner le code secret du bot avec des indices à chaque tentative
# Catégorie : Jeux
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import random
import asyncio
import discord
from discord.ext import commands
from utils.discord_utils import safe_send

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonction utilitaire pour générer un code secret et donner des indices
# ────────────────────────────────────────────────────────────────────────────────
def generate_code():
    return [str(random.randint(1, 6)) for _ in range(4)]

def check_guess(code, guess):
    exact = sum(c == g for c, g in zip(code, guess))
    partial = sum(min(code.count(d), guess.count(d)) for d in set(guess)) - exact
    return "⚪" * exact + "🔵" * partial

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Mastermind(commands.Cog):
    """
    Commande !mastermind — Joue au Mastermind contre le bot
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="mastermind", aliases=["mm"],
        help="Joue au Mastermind contre le bot (code secret de 4 chiffres entre 1 et 6).",
        description="Devine le code secret du bot en moins de 10 essais. Chaque réponse te donne des indices."
    )
    async def mastermind(self, ctx: commands.Context):
        """Commande principale Mastermind"""
        code = generate_code()
        essais_max = 10
        await safe_send(ctx.channel,
            "🧠 **Mastermind** — Devine le code secret de 4 chiffres (entre 1 et 6).\n"
            "Tu as 10 essais. Envoie simplement ta proposition (ex: `1234`).\n"
            "⚪ = bon chiffre à la bonne place\n🔵 = bon chiffre mais mauvaise place")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        for essai in range(1, essais_max + 1):
            try:
                guess_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await safe_send(ctx.channel, "⌛ Temps écoulé ! Tu n’as pas répondu à temps.")
                return

            guess = list(guess_msg.content.strip())
            if len(guess) != 4 or not all(c in "123456" for c in guess):
                await safe_send(ctx.channel, "❌ Entrée invalide. Envoie exactement 4 chiffres entre 1 et 6.")
                continue

            if guess == code:
                await safe_send(ctx.channel, f"🎉 Bravo ! Tu as trouvé le code `{''.join(code)}` en {essai} essai(s) !")
                return

            feedback = check_guess(code, guess)
            await safe_send(ctx.channel, f"❌ Mauvais code. Indices : `{feedback}` ({essai}/{essais_max})")

        await safe_send(ctx.channel, f"💀 Tu as échoué. Le code était : `{''.join(code)}`")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Mastermind(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
