import discord
from discord.ext import commands

class SayCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Fait répéter un message par le bot et supprime le message d'origine.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown de 3s
    async def say(self, ctx, *, message: str):
        try:
            # 🧽 Supprime le message d’origine
            await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de supprimer le message.")
            return
        except discord.HTTPException:
            await ctx.send("⚠️ Une erreur est survenue lors de la suppression du message.")
            return

        # 💬 Envoie le message à la place de l'utilisateur
        await ctx.send(message)

    def cog_load(self):
        self.say.category = "Général"  # ✅ Catégorie ajoutée pour la commande !help

# Chargement du module
async def setup(bot):
    await bot.add_cog(SayCommand(bot))
