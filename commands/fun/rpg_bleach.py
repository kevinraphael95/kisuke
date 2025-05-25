import discord
import json
import asyncio
from discord.ext import commands

class RPGBleach(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("data/rpg_bleach.json", "r", encoding="utf-8") as f:
            self.scenario = json.load(f)

    @commands.command(name="rpgbleach", help="Débute une histoire interactive en tant que Shinigami de Karakura.")
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)  # 5 min cooldown
    async def rpgbleach(self, ctx):
        await self.jouer_etape(ctx, "start")

    async def jouer_etape(self, ctx, etape_id):
        etape = self.scenario.get(etape_id)
        if not etape:
            await ctx.send("❌ Erreur de scénario.")
            return

        embed = discord.Embed(title="RPG Bleach", description=etape["texte"], color=discord.Color.blue())
        message = await ctx.send(embed=embed)

        emojis = []
        for choix in etape.get("choix", []):
            embed.add_field(name=choix["emoji"], value=choix["texte"], inline=False)
            emojis.append(choix["emoji"])

        await message.edit(embed=embed)
        for emoji in emojis:
            await message.add_reaction(emoji)

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in emojis

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("⏰ Tu n’as pas réagi à temps. L’histoire s’arrête ici.")
            return

        # Aller à l’étape suivante
        for choix in etape["choix"]:
            if choix["emoji"] == str(reaction.emoji):
                await self.jouer_etape(ctx, choix["suivant"])
                return

# Chargement automatique
async def setup(bot):
    cog = RPGBleach(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
