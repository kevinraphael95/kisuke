import discord
from discord.ext import commands
import asyncio
import json
import os
from supabase_client import supabase  # je suppose que c'est bien importé comme ça

SCENARIO_PATH = os.path.join("data", "rpg_bleach.json")

def load_scenario():
    with open(SCENARIO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

class RPGBleach(commands.Cog):
    """
    Commande !rpg — Lance une aventure RPG inspirée de Bleach
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.scenario = load_scenario()

    @commands.command(
        name="rpg",
        help="Commence ton aventure dans la Division Z à Karakura.",
        description="Lance une aventure interactive avec choix et sauvegarde."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rpg(self, ctx: commands.Context):
        user_id = str(ctx.author.id)

        # 🔎 Récupération de la sauvegarde Supabase (avec await)
        data = await supabase.table("rpg_save").select("*").eq("user_id", user_id).execute()
        save = data.data[0] if data.data else None
        etape = save["etape"] if save else None
        character_name = save["character_name"] if save else None
        mission = save["mission"] if save else None

        # 🔁 Reprendre la partie si déjà commencée
        if etape and character_name and mission:
            await self.jouer_etape(ctx, etape, character_name, mission)
            return

        # 🧭 Introduction et choix
        intro = self.scenario.get("intro", {})
        intro_texte = intro.get("texte", "Bienvenue dans la Division Z.")
        missions = self.scenario.get("missions", {})
        mission_keys = list(missions.keys())

        emojis = ["✏️"] + ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"][:len(mission_keys)]

        embed = discord.Embed(title="🔰 RPG Bleach - Division Z", description=intro_texte, color=discord.Color.teal())
        embed.add_field(name="✏️ Choisir un nom", value="Clique sur ✏️ pour définir le nom de ton personnage.", inline=False)
        for i, key in enumerate(mission_keys):
            m = missions[key]
            embed.add_field(name=f"{emojis[i + 1]} {m['titre']}", value=m["description"], inline=False)

        menu_msg = await ctx.send(embed=embed)
        for emoji in emojis:
            await menu_msg.add_reaction(emoji)

        temp_name = character_name or None

        def check_react(reaction, user):
            return user == ctx.author and reaction.message.id == menu_msg.id and str(reaction.emoji) in emojis

        while True:
            try:
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=300, check=check_react)
            except asyncio.TimeoutError:
                await ctx.send("⏰ Tu n’as pas réagi à temps.")
                return

            if str(reaction.emoji) == "✏️":
                name_prompt = await ctx.send("📛 Réponds à **ce message** avec le nom de ton personnage (5 minutes).")

                def check_name(m):
                    return m.author == ctx.author and m.reference and m.reference.message_id == name_prompt.id

                try:
                    msg = await self.bot.wait_for("message", timeout=300.0, check=check_name)
                    temp_name = msg.content.strip()
                    await ctx.send(f"✅ Ton nom est enregistré : **{temp_name}**")
                except asyncio.TimeoutError:
                    await ctx.send("⏰ Temps écoulé pour le nom.")
                continue

            if not temp_name:
                await ctx.send("❗ Choisis ton nom avec ✏️ avant de commencer une mission.")
                continue

            index = emojis.index(str(reaction.emoji)) - 1
            mission_id = mission_keys[index]
            start_etape = missions[mission_id]["start"]

            # 🔄 Sauvegarde avec await
            await supabase.table("rpg_save").upsert({
                "user_id": user_id,
                "username": ctx.author.name,
                "character_name": temp_name,
                "mission": mission_id,
                "etape": start_etape
            }, on_conflict=["user_id"]).execute()

            await self.jouer_etape(ctx, start_etape, temp_name, mission_id)
            return

    async def jouer_etape(self, ctx: commands.Context, etape_id: str, character_name: str, mission_id: str):
        etape = self.scenario.get(etape_id)
        if not etape:
            await ctx.send("❌ Étape du scénario introuvable.")
            return

        texte = etape["texte"].replace("{nom}", character_name)
        embed = discord.Embed(
            title=f"🧭 Mission : {self.scenario['missions'][mission_id]['titre']}",
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

        def check_choice(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in emojis

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=300.0, check=check_choice)
        except asyncio.TimeoutError:
            await ctx.send("⏰ Tu n’as pas réagi à temps.")
            return

        for choix in etape["choix"]:
            if choix["emoji"] == str(reaction.emoji):
                next_etape = choix["suivant"]

                await supabase.table("rpg_save").upsert({
                    "user_id": str(ctx.author.id),
                    "username": ctx.author.name,
                    "character_name": character_name,
                    "mission": mission_id,
                    "etape": next_etape
                }, on_conflict=["user_id"]).execute()

                await self.jouer_etape(ctx, next_etape, character_name, mission_id)
                return

async def setup(bot: commands.Bot):
    cog = RPGBleach(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "VAACT"
    await bot.add_cog(cog)
