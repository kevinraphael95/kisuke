import discord
from discord.ext import commands
import aiohttp
import asyncio
import re

# ──────────────────────────────────────────────────────────────
# 🔧 COG : PenduCommand
# ──────────────────────────────────────────────────────────────
class PenduCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot  # 🔌 Stocke l'instance du bot

    # ──────────────────────────────────────────────────────────
    # 🔹 COMMANDE : !pendu
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="pendu",
        aliases=["hangman"],
        help="🎮 Lance une partie de pendu avec un mot aléatoire."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🧊 Anti-spam
    async def pendu(self, ctx: commands.Context):
        # 📥 Récupère un mot aléatoire depuis motsaleatoires.com
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.motsaleatoires.com/") as response:
                if response.status != 200:
                    await ctx.send("❌ Impossible de récupérer un mot aléatoire.")
                    return
                text = await response.text()
                match = re.search(r'<div class="mot">([^<]+)</div>', text)
                if not match:
                    await ctx.send("❌ Aucun mot trouvé sur le site.")
                    return
                word = match.group(1).strip().lower()

        # 🧠 Initialisation du jeu
        guessed = set()
        tries = 6
        display = ["_" if c.isalpha() else c for c in word]

        def format_display():
            return " ".join(display)

        await ctx.send(f"🎯 Mot à deviner : {format_display()}\n🔁 Tentatives restantes : {tries}")

        def check(m):
            return (
                m.channel == ctx.channel
                and m.author == ctx.author
                and len(m.content) == 1
                and m.content.isalpha()
            )

        while tries > 0 and "_" in display:
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await ctx.send("⏰ Temps écoulé ! Le mot était : **{}**".format(word))
                return

            guess = msg.content.lower()
            if guess in guessed:
                await ctx.send("⚠️ Lettre déjà proposée.")
                continue

            guessed.add(guess)
            if guess in word:
                for idx, char in enumerate(word):
                    if char == guess:
                        display[idx] = guess
                await ctx.send(f"✅ Bonne lettre ! {format_display()}")
            else:
                tries -= 1
                await ctx.send(f"❌ Mauvaise lettre. {format_display()}\n🔁 Tentatives restantes : {tries}")

        if "_" not in display:
            await ctx.send(f"🎉 Félicitations ! Vous avez deviné le mot : **{word}**")
        else:
            await ctx.send(f"💀 Perdu ! Le mot était : **{word}**")

    # 🏷️ Catégorisation pour affichage personnalisé dans !help
    def cog_load(self):
        self.pendu.category = "Jeux"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(PenduCommand(bot))
    print("✅ Cog chargé : PenduCommand (catégorie = Jeux)")
