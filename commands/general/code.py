import discord
from discord.ext import commands

# Cette commande affiche le lien vers le dépôt GitHub du bot
class CodeCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="code", help="Affiche le lien du code du bot sur GitHub.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 Cooldown utilisateur de 3s
    async def code(self, ctx):
        await ctx.send("🔗 Code source du bot : https://github.com/kevinraphael95/bleach-discord-bot-test")

    # 🛠️ Ajout de la catégorie une fois le Cog chargé
    def cog_load(self):
        self.code.category = "Général"

# Chargement automatique par le bot
async def setup(bot):
    await bot.add_cog(CodeCommand(bot))
