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
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rpg(self, ctx):
        user_id = str(ctx.author.id)
        save = supabase.table("rpg_save").select("*").eq("user_id", user_id).execute().data
        save = save[0] if save else None

        # Demander nom du perso si non défini
        if not save or not save.get("character_name"):
            prompt = await ctx.send(f"{ctx.author.mention}, comment veux-tu appeler ton personnage Shinigami ? (Réponds à **ce message** dans les 5 minutes)")

            def check(m):
                return m.author == ctx.author and m.reference and m.reference.message_id == prompt.id

            try:
                msg = await self.bot.wait_for("message", timeout=300.0, check=check)
            except asyncio.TimeoutError:
                await ctx.send("⏰ Tu n'as pas répondu à temps. Relance la commande `!rpg`.")
                return

            character_name = msg.content.strip()
            # Choix d'une mission
            missions = self.scenario.get("missions", {})
            if not missions:
                await ctx.send("❌ Aucune mission disponible.")
                return

            embed = discord.Embed(title="📜 Missions disponibles", description="Choisis une mission en réagissant :", color=discord.Color.teal())
            emoji_list = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
            mission_map = {}

            for i, (key, mission) in enumerate(missions.items()):
                emoji = emoji_list[i]
                embed.add_field(name=f"{emoji} {mission['titre']}", value=mission['description'], inline=False)
                mission_map[emoji] = key

            mission_msg = await ctx.send(embed=embed)
            for emoji in mission_map:
                await mission_msg.add_reaction(emoji)

            def mission_check(reaction, user):
                return user == ctx.author and reaction.message.id == mission_msg.id and str(reaction.emoji) in mission_map

            try:
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=300.0, check=mission_check)
            except asyncio.TimeoutError:
                await ctx.send("⏰ Temps écoulé. Relance `!rpg`.")
                return

            mission_id = mission_map[str(reaction.emoji)]
            etape = self.scenario["missions"][mission_id]["start"]

            supabase.table("rpg_save").upsert({
                "user_id": user_id,
                "username": ctx.author.name,
                "character_name": character_name,
                "etape": etape,
                "mission_id": mission_id
            }, on_conflict=["user_id"]).execute()

            await ctx.send(f"🎖️ Mission choisie : **{self.scenario['missions'][mission_id]['titre']}**")
        else:
            etape = save["etape"]
            character_name = save["character_name"]
            mission_id = save.get("mission_id")

        await self.jouer_etape(ctx, etape, character_name)

    async def jouer_etape(self, ctx, etape_id, character_name):
        etape = self.scenario.get(etape_id)
        if not etape:
            await ctx.send("❌ Erreur : cette étape du scénario est introuvable.")
            return

        texte = etape["texte"].replace("{nom}", character_name)

        embed = discord.Embed(
            title="🗺️ RPG Bleach - Brigade de Karakura",
            description=texte,
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
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in emojis

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=300.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("⏰ Temps écoulé. Ton aventure reprendra plus tard.")
            return

        for choix in etape["choix"]:
            if choix["emoji"] == str(reaction.emoji):
                next_etape = choix["suivant"]
                supabase.table("rpg_save").upsert({
                    "user_id": str(ctx.author.id),
                    "username": ctx.author.name,
                    "etape": next_etape,
                    "character_name": character_name
                }, on_conflict=["user_id"]).execute()

                await self.jouer_etape(ctx, next_etape, character_name)
                return

# Chargement automatique
async def setup(bot):
    cog = RPG(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
