import discord
import json
import asyncio
from discord.ext import commands
from supabase_client import supabase

class RPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("data/rpg_bleach.json", "r", encoding="utf-8") as f:
            self.scenario = json.load(f)

    @commands.command(name="rpg", help="Débute ou continue ton histoire de Shinigami à Karakura.")
    @commands.cooldown(rate=1, per=300, type=commands.BucketType.user)  # cooldown de 5 min
    async def rpg(self, ctx):
        user_id = str(ctx.author.id)

        # Récupère l'étape sauvegardée
        data = supabase.table("rpg_save").select("etape").eq("user_id", user_id).execute()
        etape = data.data[0]["etape"] if data.data else "start"

        await self.jouer_etape(ctx, etape)

    async def jouer_etape(self, ctx, etape_id):
        etape = self.scenario.get(etape_id)
        if not etape:
            await ctx.send("❌ Erreur : cette étape du scénario est introuvable.")
            return

        embed = discord.Embed(
            title="🗺️ RPG Bleach - Brigade de Karakura",
            description=etape["texte"],
            color=discord.Color.dark_purple()
        )

        emojis = []
        for choix in etape.get("choix", []):
            embed.add_field(name=choix["emoji"], value=choix["texte"], inline=False)
            emojis.append(choix["emoji"])

        message = await ctx.send(embed=embed)
        for emoji in emojis:
            await message.add_reaction(emoji)

        def check(reaction, user):
            return (
                user == ctx.author and
                reaction.message.id == message.id and
                str(reaction.emoji) in emojis
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("⏰ Temps écoulé. Ton aventure reprendra plus tard.")
            return

        # Trouver l'étape suivante
        for choix in etape["choix"]:
            if choix["emoji"] == str(reaction.emoji):
                next_etape = choix["suivant"]

                # Sauvegarder progression
                supabase.table("rpg_save").upsert({
                    "user_id": str(ctx.author.id),
                    "username": str(ctx.author.name),
                    "etape": next_etape
                }).execute()

                await self.jouer_etape(ctx, next_etape)
                return

# Chargement automatique
async def setup(bot):
    cog = RPG(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
