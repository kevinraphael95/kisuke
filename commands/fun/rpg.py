# ────────────────────────────────────────────────────────────────
# 📜 RPG BLEACH - SYSTEME D'AVENTURE INTERACTIF VIA REACTIONS
# ────────────────────────────────────────────────────────────────

import discord
import json
import asyncio
from discord.ext import commands
from supabase_client import supabase

# ────────────────────────────────────────────────────────────────
# 📦 COG RPG PRINCIPAL
# ────────────────────────────────────────────────────────────────
class RPG(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("data/rpg_bleach.json", "r", encoding="utf-8") as f:
            self.scenario = json.load(f)

    # ──────────────────────────────────────────────────────
    # 🎮 COMMANDE PRINCIPALE : !rpg
    # Lance ou continue l'aventure RPG de l'utilisateur
    # ──────────────────────────────────────────────────────
    @commands.command(name="rpg", help="Commence ton aventure dans la Division Z à Karakura.")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def rpg(self, ctx):
        user_id = str(ctx.author.id)

        # 🔎 Récupération de la sauvegarde Supabase
        data = supabase.table("rpg_save").select("*").eq("user_id", user_id).execute()
        save = data.data[0] if data.data else None
        etape = save["etape"] if save else None
        character_name = save["character_name"] if save else None
        mission = save["mission"] if save else None

        # 🔁 Si une sauvegarde existe, on continue l’aventure
        if etape and character_name and mission:
            await self.jouer_etape(ctx, etape, character_name, mission)
            return

        # 🧭 Écran d’introduction
        intro = self.scenario.get("intro", {})
        intro_texte = intro.get("texte", "Bienvenue dans la Division Z.")
        missions = self.scenario.get("missions", {})
        mission_keys = list(missions.keys())

        emojis = ["✏️"] + ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"][:len(mission_keys)]

        embed = discord.Embed(
            title="🔰 RPG Bleach - Division Z",
            description=intro_texte,
            color=discord.Color.teal()
        )
        embed.add_field(name="✏️ Choisir un nom", value="Clique sur ✏️ pour définir le nom de ton personnage.", inline=False)
        for i, key in enumerate(mission_keys):
            mission = missions[key]
            embed.add_field(name=f"{emojis[i + 1]} {mission['titre']}", value=mission["description"], inline=False)

        menu_msg = await ctx.send(embed=embed)
        for emoji in emojis:
            await menu_msg.add_reaction(emoji)

        temp_name = character_name or None

        # 📩 Attente d'une réaction utilisateur
        def check_react(reaction, user):
            return user == ctx.author and reaction.message.id == menu_msg.id and str(reaction.emoji) in emojis

        while True:
            try:
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=300, check=check_react)
            except asyncio.TimeoutError:
                await ctx.send("⏰ Tu n’as pas réagi à temps.")
                return

            # ✏️ Gestion du nom personnalisé
            if str(reaction.emoji) == "✏️":
                name_prompt = await ctx.send("📛 Réponds à **ce message** avec ton nom de personnage (5 minutes).")

                def check_name(m):
                    return m.author == ctx.author and m.reference and m.reference.message_id == name_prompt.id

                try:
                    msg = await self.bot.wait_for("message", timeout=300.0, check=check_name)
                    temp_name = msg.content.strip()
                    await ctx.send(f"✅ Ton nom est enregistré : **{temp_name}**")
                except asyncio.TimeoutError:
                    await ctx.send("⏰ Temps écoulé pour le nom.")
                continue

            # ⛔ Nom requis avant mission
            if not temp_name:
                await ctx.send("❗ Choisis ton nom avec ✏️ avant de commencer une mission.")
                continue

            # 🧭 Démarrage de mission
            index = emojis.index(str(reaction.emoji)) - 1
            mission_id = mission_keys[index]
            start_etape = missions[mission_id]["start"]

            # 💾 Sauvegarde dans Supabase
            supabase.table("rpg_save").upsert({
                "user_id": user_id,
                "username": ctx.author.name,
                "character_name": temp_name,
                "mission": mission_id,
                "etape": start_etape
            }, on_conflict=["user_id"]).execute()

            await self.jouer_etape(ctx, start_etape, temp_name, mission_id)
            return

    # ──────────────────────────────────────────────────────
    # 🧩 MOTEUR D'ÉTAPE : Affiche une étape, attends une décision
    # ──────────────────────────────────────────────────────
    async def jouer_etape(self, ctx, etape_id, character_name, mission_id):
        etape = self.scenario.get(etape_id)
        if not etape:
            await ctx.send("❌ Étape du scénario introuvable.")
            return

        # 📜 Texte de l’étape
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

        # 🎯 Attente de choix utilisateur
        def check_choice(reaction, user):
            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in emojis

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=300.0, check=check_choice)
        except asyncio.TimeoutError:
            await ctx.send("⏰ Tu n’as pas réagi à temps.")
            return

        # ⏩ Transition vers l'étape suivante
        for choix in etape["choix"]:
            if choix["emoji"] == str(reaction.emoji):
                next_etape = choix["suivant"]

                supabase.table("rpg_save").upsert({
                    "user_id": str(ctx.author.id),
                    "username": ctx.author.name,
                    "character_name": character_name,
                    "mission": mission_id,
                    "etape": next_etape
                }, on_conflict=["user_id"]).execute()

                await self.jouer_etape(ctx, next_etape, character_name, mission_id)
                return

# ──────────────────────────────────────────────────────
# 🔌 CHARGEMENT DU COG
# ──────────────────────────────────────────────────────
async def setup(bot):
    cog = RPG(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
