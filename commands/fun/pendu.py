# ──────────────────────────────────────────────────────────────
# 📁 pendu
# ──────────────────────────────────────────────────────────────

# ───────────────────────────────────────────────────────────────────────────────
# 📦 Cog principal — Commande !pendu
# ───────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import asyncio
from random_words_generator.words import generate_random_words

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
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)  # 🧊 Anti-spam
    async def pendu(self, ctx: commands.Context):
        # 🎯 Génère un mot français aléatoire
        try:
            mot = generate_random_words(1)[0].lower()
        except Exception as e:
            await ctx.send("❌ Impossible de générer un mot aléatoire.")
            return

        lettres_trouvees = set()
        lettres_ratees = set()
        tentatives_restantes = 6

        def afficher_mot():
            return ' '.join([lettre if lettre in lettres_trouvees else '_' for lettre in mot])

        await ctx.send(f"🎮 **Jeu du Pendu**\nMot à deviner : `{afficher_mot()}`\nTentatives restantes : {tentatives_restantes}")

        def check(message):
            return (
                message.author == ctx.author
                and message.channel == ctx.channel
                and len(message.content) == 1
                and message.content.isalpha()
            )

        while tentatives_restantes > 0:
            try:
                msg = await self.bot.wait_for("message", check=check, timeout=60.0)
                lettre = msg.content.lower()

                if lettre in lettres_trouvees or lettre in lettres_ratees:
                    await ctx.send("⚠️ Lettre déjà proposée.")
                    continue

                if lettre in mot:
                    lettres_trouvees.add(lettre)
                    await ctx.send(f"✅ Bien joué ! `{afficher_mot()}`")
                else:
                    lettres_ratees.add(lettre)
                    tentatives_restantes -= 1
                    await ctx.send(f"❌ Mauvais choix. Tentatives restantes : {tentatives_restantes}\nMot : `{afficher_mot()}`")

                if all(l in lettres_trouvees for l in mot):
                    await ctx.send(f"🎉 Félicitations ! Vous avez deviné le mot : **{mot}**")
                    return

            except asyncio.TimeoutError:
                await ctx.send("⏰ Temps écoulé !")
                return

        await ctx.send(f"💀 Partie terminée. Le mot était : **{mot}**")

    # 🏷️ Catégorisation pour affichage personnalisé dans !help
    def cog_load(self):
        self.pendu.category = "Jeux"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(PenduCommand(bot))
    print("✅ Cog chargé : PenduCommand (catégorie = Jeux)")
