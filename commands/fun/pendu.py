import discord
from discord.ext import commands
from random_words_generator.words import generate_random_words
import asyncio
import random
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
        help="🎮 Lance une partie de pendu avec un mot français aléatoire."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🧊 Anti-spam
    async def pendu(self, ctx: commands.Context):
        # 📥 Génère un mot aléatoire en français
        mots = generate_random_words(1)
        if not mots:
            await ctx.send("❌ Erreur lors de la génération du mot.")
            return

        mot = mots[0].lower()
        mot = re.sub(r"[^a-zàâçéèêëîïôûùüÿñæœ]", "", mot)  # Nettoie les caractères non alpha

        # 🎯 Initialisation
        lettres_trouvees = set()
        lettres_ratees = set()
        tries = 6
        affichage = ["_" if c.isalpha() else c for c in mot]

        def format_affichage():
            return " ".join(affichage)

        await ctx.send(f"🎯 Mot à deviner : `{format_affichage()}`\n🔁 Tentatives restantes : **{tries}**")

        def check(message):
            return (
                message.channel == ctx.channel
                and message.author == ctx.author
                and len(message.content) == 1
                and message.content.isalpha()
            )

        while tries > 0 and "_" in affichage:
            try:
                msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ Temps écoulé ! Le mot était : **{mot}**")
                return

            lettre = msg.content.lower()

            if lettre in lettres_trouvees | lettres_ratees:
                await ctx.send("⚠️ Lettre déjà proposée.")
                continue

            if lettre in mot:
                lettres_trouvees.add(lettre)
                for i, c in enumerate(mot):
                    if c == lettre:
                        affichage[i] = lettre
                await ctx.send(f"✅ Bien vu ! `{format_affichage()}`")
            else:
                lettres_ratees.add(lettre)
                tries -= 1
                await ctx.send(f"❌ Raté. `{format_affichage()}`\n🔁 Tentatives restantes : **{tries}**")

        if "_" not in affichage:
            await ctx.send(f"🎉 Bravo {ctx.author.mention} ! Tu as trouvé le mot : **{mot}**")
        else:
            await ctx.send(f"💀 Dommage ! Le mot était : **{mot}**")

    # 🏷️ Catégorisation pour affichage personnalisé dans !help
    def cog_load(self):
        self.pendu.category = "Jeux"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(PenduCommand(bot))
    print("✅ Cog chargé : PenduCommand (catégorie = Jeux)")
