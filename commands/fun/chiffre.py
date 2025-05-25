import asyncio
import random
import discord
from discord.ext import commands

# Suivi des jeux actifs par salon
active_games = {}

class ChiffreCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="chiffre", help="Devine un nombre entre 1 et 100.")
    async def chiffre(self, ctx):
        if ctx.channel.id in active_games:
            await ctx.send("⚠️ Un jeu est déjà en cours dans ce salon. Utilisez `!cancel` pour l'annuler.")
            return

        number = random.randint(1, 100)
        await ctx.send(
            f"🎯 J'ai choisi un nombre entre 1 et 100. Le premier à répondre avec le bon nombre **dans ce salon** gagne ! Vous avez 1 heure.\n"
            f"🔍 (Réponse test : **{number}**)"  # Tu peux commenter cette ligne si tu veux désactiver le spoil
        )

        async def wait_for_answer():
            def check(m):
                return (
                    m.channel == ctx.channel and
                    m.author != self.bot.user and
                    m.content.isdigit() and
                    int(m.content) == number
                )
            try:
                msg = await self.bot.wait_for("message", timeout=3600.0, check=check)
                await ctx.send(f"🎉 Bravo {msg.author.mention}, tu as trouvé le nombre **{number}** !")
            except asyncio.TimeoutError:
                await ctx.send(f"⏰ Temps écoulé ! Personne n'a trouvé le nombre. C'était **{number}**.")
            finally:
                active_games.pop(ctx.channel.id, None)

        task = asyncio.create_task(wait_for_answer())
        active_games[ctx.channel.id] = task

    @commands.command(name="cancel", help="Annule le jeu de nombre dans ce salon.")
    async def cancel(self, ctx):
        task = active_games.pop(ctx.channel.id, None)
        if task:
            task.cancel()
            await ctx.send("🚫 Le jeu a été annulé dans ce salon.")
        else:
            await ctx.send("❌ Aucun jeu en cours à annuler ici.")

# Chargement automatique + ajout de catégorie
async def setup(bot):
    cog = ChiffreCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
