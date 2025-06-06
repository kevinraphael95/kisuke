# ──────────────────────────────────────────────────────────────
# CHIFFRE
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import asyncio
import random
import discord
from discord.ext import commands

# 📌 Dictionnaire global pour suivre les jeux actifs par salon
active_games = {}

# ──────────────────────────────────────────────────────────────
# 🎮 COG : ChiffreCommand — Jeu de devinette numérique
# ──────────────────────────────────────────────────────────────
class ChiffreCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # 🔌 Stocke l'instance du bot

    # ──────────────────────────────────────────────────────────
    # 🎯 COMMANDE : !chiffre
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="chiffre",
        help="Devine un nombre entre 1 et 100. Le premier à trouver gagne !"
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 Anti-spam : 3s
    async def chiffre(self, ctx: commands.Context):
        # 🔁 Empêche plusieurs jeux dans le même salon
        if ctx.channel.id in active_games:
            await ctx.send("⚠️ Un jeu est déjà en cours ici. Tape `!cancel` pour le stopper.")
            return

        # 🎲 Choix aléatoire d’un nombre
        number = random.randint(1, 100)
        await ctx.send(
            f"🎯 J'ai choisi un nombre entre **1 et 100**.\n"
            f"💡 Le **premier** à le deviner dans ce salon gagne !\n"
            f"⏳ Temps limite : 1 heure.\n"
            f"🔍 *(Réponse de test : {number})*"  # 🔧 Pour dev, commente cette ligne en prod
        )

        # 🎯 Fonction asynchrone pour attendre la bonne réponse
        async def wait_for_answer():
            def check(message: discord.Message):
                return (
                    message.channel == ctx.channel and
                    message.author != self.bot.user and
                    message.content.isdigit() and
                    int(message.content) == number
                )

            try:
                msg = await self.bot.wait_for("message", timeout=3600.0, check=check)
                await ctx.send(f"🎉 Bravo {msg.author.mention}, tu as trouvé le nombre **{number}** !")
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ Temps écoulé ! Personne n'a trouvé le nombre. C'était **{number}**.")
            finally:
                active_games.pop(ctx.channel.id, None)  # Nettoyage du jeu

        # 🔄 Enregistre la tâche dans le dictionnaire des jeux actifs
        task = asyncio.create_task(wait_for_answer())
        active_games[ctx.channel.id] = task

    # ──────────────────────────────────────────────────────────
    # ⛔ COMMANDE : !cancel — Annule un jeu actif dans ce salon
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="cancel",
        help="Annule le jeu de nombre en cours dans ce salon."
    )
    async def cancel(self, ctx: commands.Context):
        task = active_games.pop(ctx.channel.id, None)
        if task:
            task.cancel()
            await ctx.send("🚫 Le jeu a été annulé dans ce salon.")
        else:
            await ctx.send("❌ Aucun jeu actif à annuler ici.")

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR LE CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot):
    cog = ChiffreCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"  # ✅ Pour que !help affiche la commande correctement
    await bot.add_cog(cog)
    print("✅ Cog chargé : ChiffreCommand (catégorie = Fun)")
