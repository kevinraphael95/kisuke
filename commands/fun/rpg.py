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

        # Cherche une sauvegarde existante
        data = supabase.table("rpg_save").select("*").eq("user_id", user_id).execute()
        save = data.data[0] if data.data else None
        etape = save["etape"] if save else "start"
        character_name = save["character_name"] if save and "character_name" in save else None

        # Si pas encore de nom, demander au joueur
        if etape == "start" and not character_name:
            prompt = await ctx.send(f"{ctx.author.mention}, comment veux-tu appeler ton personnage Shinigami ? (Réponds à **ce message** dans les 5 minutes)")

            def check(m):
                return (
                    m.author == ctx.author and
                    m.reference and m.reference.message_id == prompt.id
                )

            try:
                msg = await self.bot.wait_for("message", timeout=300.0, check=check)
                character_name = msg.content.strip()

                # Créer la sauvegarde
                supabase.table("rpg_save").upsert({
                    "user_id": user_id,
                    "username": ctx.author.name,
                    "etape": "start",
                    "character_name": character_name
                }, on_conflict=["user_id"]).execute()

                await ctx.send(f"✨ Ton personnage s'appelle **{character_name}**. Bonne aventure !")
            except asyncio.TimeoutError:
                await ctx.send("⏰ Tu n'as pas répondu à temps. Relance la commande `!rpg` pour recommencer.")
                return

        # Lancer l’étape
        await self.jouer_etape(ctx, etape, character_name)

    async def jouer_etape(self, ctx, etape_id, character_name):
        etape = self.scenario.get(etape_id)
        if not etape:
            await ctx.send("❌ Erreur : cette étape du scénario est introuvable.")
            return

        # Remplacement du nom dans le texte
        texte = etape["texte"].replace("{nom}", character_name or ctx.author.display_name)

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
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=300.0, check=check)  # ⏳ 5 min
        except asyncio.TimeoutError:
            await ctx.send("⏰ Temps écoulé. Ton aventure reprendra plus tard.")
            return

        for choix in etape["choix"]:
            if choix["emoji"] == str(reaction.emoji):
                next_etape = choix["suivant"]

                # Mise à jour de la sauvegarde
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
