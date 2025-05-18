from keep_alive import keep_alive  # Démarre le serveur web pour maintenir le bot en ligne

import io
import os
import ast
import random
import asyncio
import aiohttp
from datetime import datetime
from discord.ext import tasks, commands
import discord
from database import init_db, get_reiatsu, add_reiatsu
from dotenv import load_dotenv
from database import set_reiatsu_channel, get_reiatsu_channel


# Répertoire de travail
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Charger les variables d’environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Préfixe dynamique
def get_prefix(bot, message):
    return os.getenv("COMMAND_PREFIX", "!")

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

# Création du bot
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# Liste des personnages Bleach
def load_characters(filename="bleach_characters.txt"):
    with open(filename, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

bleach_characters = load_characters()

# Événement : bot prêt
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="en train de coder !"))
    print(f"✅ Connecté en tant que {bot.user.name}")
    reset_daily_counter.start()
    spawn_reiatsu_event.start()

# Répondre à une mention du bot
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.strip() in (f"<@{bot.user.id}>", f"<@!{bot.user.id}>"):
        prefix = get_prefix(bot, message)
        cmds = [command.name for command in bot.commands if not command.hidden]
        await message.channel.send(
            f"👋 Mon préfixe est : `{prefix}`\n📜 Commandes disponibles : "
            + ", ".join(f"`{prefix}{cmd}`" for cmd in cmds)
        )
    else:
        await bot.process_commands(message)

#############################
########## daily reiatsu ##########
#############################

import asyncio
import random
from datetime import datetime
from discord.ext import commands, tasks
import discord

MAX_EVENTS_PER_DAY = 4
REACTION_EMOJI = "⚡"

# 👉 Commande pour définir le salon de spawn
@bot.command(name="setreiatsu", help="Définit ce salon pour les apparitions de Reiatsu (admin uniquement).")
@commands.has_permissions(administrator=True)
async def setreiatsu(ctx):
    await asyncio.to_thread(set_reiatsu_channel, ctx.guild.id, ctx.channel.id)
    await ctx.send(f"✅ Les Reiatsu apparaîtront désormais dans {ctx.channel.mention}.")
setreiatsu.category = "Reiatsu"

# 👉 Compteur d'événements par jour
events_today = 0
today_date = datetime.now().date()

# ⏲️ Reset automatique chaque jour
@tasks.loop(minutes=1)
async def reset_daily_counter():
    global events_today, today_date
    now = datetime.now().date()
    if now != today_date:
        today_date = now
        events_today = 0
        print("🔁 Compteur Reiatsu remis à zéro pour la journée.")

# 🌩️ Spawn aléatoire de Reiatsu
@tasks.loop(seconds=60)
async def spawn_reiatsu_event():
    global events_today
    if events_today >= MAX_EVENTS_PER_DAY:
        return

    if random.randint(1, 60) == 1:  # ~1 fois par heure
        events_today += 1

        for guild in bot.guilds:
            channel_id = await asyncio.to_thread(get_reiatsu_channel, guild.id)
            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)
            if not channel or not channel.permissions_for(guild.me).send_messages:
                continue

            print(f"⚡ Apparition de Reiatsu dans {guild.name}#{channel.name}")
            msg = await channel.send("⚡ **Un nuage de Reiatsu apparaît !** Réagis avec ⚡ pour le collecter !")
            await msg.add_reaction(REACTION_EMOJI)

            def check(reaction, user):
                return (
                    str(reaction.emoji) == REACTION_EMOJI
                    and reaction.message.id == msg.id
                    and not user.bot
                )

            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=7200.0, check=check)
            except asyncio.TimeoutError:
                await channel.send("⏰ Personne n'a collecté le Reiatsu cette fois...")
                await msg.clear_reactions()
            else:
                await asyncio.to_thread(add_reiatsu, user.id, 1)
                total = await asyncio.to_thread(get_reiatsu, user.id)
                await channel.send(f"🎉 {user.mention} a collecté 1 Reiatsu ! Total: {total}")
                await msg.clear_reactions()

            break  # Un seul événement à la fois

# 👉 Commande pour consulter son total
@bot.command(name="reiatsu", help="Affiche le total de Reiatsu que tu as collecté.")
async def reiatsu(ctx):
    total = await asyncio.to_thread(get_reiatsu, ctx.author.id)
    await ctx.send(f"{ctx.author.mention}, tu as {total} Reiatsu.")
reiatsu.category = "Reiatsu"

# 👉 Commande pour tester manuellement (admin)
@bot.command(name="testreiatsu", help="Force l'apparition d'un nuage de Reiatsu pour test (admin uniquement).")
@commands.has_permissions(administrator=True)
async def testreiatsu(ctx):
    channel = ctx.channel
    msg = await channel.send("⚡ **Un nuage de Reiatsu apparaît !** Réagis avec ⚡ pour le collecter !")
    await msg.add_reaction(REACTION_EMOJI)

    def check(reaction, user):
        return (
            str(reaction.emoji) == REACTION_EMOJI
            and reaction.message.id == msg.id
            and not user.bot
        )

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=7200.0, check=check)
    except asyncio.TimeoutError:
        await channel.send("⏰ Personne n'a collecté le Reiatsu cette fois...")
        await msg.clear_reactions()
    else:
        await asyncio.to_thread(add_reiatsu, user.id, 1)
        total = await asyncio.to_thread(get_reiatsu, user.id)
        await channel.send(f"🎉 {user.mention} a collecté 1 Reiatsu ! Total: {total}")
        await msg.clear_reactions()
testreiatsu.category = "Reiatsu"

@testreiatsu.error
async def testreiatsu_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Tu dois être **administrateur** pour utiliser cette commande.")
    else:
        raise error

        
#############################
########## général ##########
#############################

########## code ##########
@bot.command(name="code", help="Envoie le lien du code source du bot.")
async def code(ctx):
    await ctx.send("📂 Voici le code source du bot sur GitHub :\n🔗 https://github.com/kevinraphael95/bleach-discord-bot-test")
code.category = "Général"


########## 👋 Hello ##########
@bot.command(help="Affiche un message de bienvenue aléatoire.")
async def hello(ctx):
    try:
        with open("hello_messages.txt", "r", encoding="utf-8") as f:
            messages = [line.strip() for line in f if line.strip()]
        if messages:
            await ctx.send(random.choice(messages))
        else:
            await ctx.send("👋 Hello, je suis en ligne (mais sans message personnalisé) !")
    except FileNotFoundError:
        await ctx.send("❌ Fichier `hello_messages.txt` introuvable.")
hello.category = "Général"

# 🏓 Ping avec Embed + alias "test"
@bot.command(aliases=["test"], help="Répond avec la latence du bot.")
async def ping(ctx):
    latence = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong !",
        description=f"📶 Latence : `{latence} ms`",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)
ping.category = "Général"

########## 📘 Commande : help ##########
@bot.command(name="help", help="Affiche la liste des commandes ou les infos sur une commande spécifique.")
async def help_command(ctx, commande: str = None):
    prefix = get_prefix(bot, ctx.message)

    if commande is None:
        categories = {
            "Général": [],
            "Fun": [],
            "Admin": [],
            "Reiatsu": [],
            "Autres": []
        }

        # Répartir les commandes dans leurs catégories
        for cmd in bot.commands:
            if cmd.hidden:
                continue
            cat = getattr(cmd, "category", "Autres")
            categories.setdefault(cat, []).append(cmd)

        embed = discord.Embed(title="📜 Commandes par catégorie", color=discord.Color.blue())

        # Parcourir les catégories dans un ordre fixe
        for cat in ["Général", "Fun", "Admin", "Reiatsu", "Autres"]:
            cmds = categories.get(cat, [])
            if cmds:
                # Trier les commandes par ordre alphabétique du nom
                cmds.sort(key=lambda c: c.name)
                liste = "\n".join(f"`{prefix}{cmd.name}` : {cmd.help or 'Pas de description.'}" for cmd in cmds)
                embed.add_field(name=f"📂 {cat}", value=liste, inline=False)

        embed.set_footer(text=f"Utilise {prefix}help <commande> pour plus de détails.")
        await ctx.send(embed=embed)

    else:
        cmd = bot.get_command(commande)
        if cmd is None:
            await ctx.send(f"❌ La commande `{commande}` n'existe pas.")
        else:
            embed = discord.Embed(
                title=f"Aide pour `{prefix}{cmd.name}`",
                color=discord.Color.green()
            )
            embed.add_field(name="Description", value=cmd.help or "Pas de description.", inline=False)
            if cmd.aliases:
                embed.add_field(name="Alias", value=", ".join(f"`{a}`" for a in cmd.aliases), inline=False)
            embed.set_footer(text="Paramètres entre < > sont obligatoires, ceux entre [ ] sont optionnels.")
            await ctx.send(embed=embed)
help_command.category = "Général"

########## 🗣️ Say ##########
@bot.command(help="Fait répéter un message par le bot et supprime le message d'origine.")
async def say(ctx, *, message: str):
    try:
        await ctx.message.delete()
    except discord.Forbidden:
        await ctx.send("❌ Je n'ai pas la permission de supprimer le message.")
        return
    except discord.HTTPException:
        await ctx.send("⚠️ Une erreur est survenue lors de la suppression du message.")
        return
    await ctx.send(message)
say.category = "Général"

#############################
########## fun ##########
#############################

########## dog ##########
@bot.command()
async def dog(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://dog.ceo/api/breeds/image/random") as response:
            if response.status == 200:
                data = await response.json()
                image_url = data["message"]
                await ctx.send(f"Voici un toutou aléatoire ! 🐶\n{image_url}")
            else:
                await ctx.send("Impossible de récupérer une image de chien 😢")
dog.category = "Fun"

########## cat ##########
@bot.command()
async def cat(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://cataas.com/cat") as response:
            if response.status == 200:
                image_data = await response.read()
                image_file = discord.File(io.BytesIO(image_data), filename="cat.jpg")
                await ctx.send("Voici un minou aléatoire ! 🐱", file=image_file)
            else:
                await ctx.send("Impossible de récupérer une image de chat 😿")

cat.category = "Fun"



########## combat ##########
@bot.command(name="combat", help="Simule un combat entre 2 personnages de Bleach avec système de stats et énergie.")
async def combat_bleach(ctx):
    try:
        with open("bleach_personnages.txt", "r", encoding="utf-8") as f:
            lignes = [line.strip() for line in f if line.strip()]

        if len(lignes) < 2:
            await ctx.send("❌ Pas assez de personnages dans le fichier.")
            return

        perso1_data, perso2_data = random.sample(lignes, 2)

        def parse_perso(data):
            parts = data.split("|")
            nom = parts[0]
            stats_raw = parts[1]
            attaques_raw = parts[2:]

            stats = dict(zip(
                ["attaque", "défense", "mobilité", "pression", "intelligence", "force"],
                map(int, stats_raw.split(","))
            ))

            attaques = []
            for att in attaques_raw:
                nom_att, degats, cout, effet, type_att = att.split(":")
                attaques.append({
                    "nom": nom_att,
                    "degats": int(degats),
                    "cout": int(cout),
                    "effet": effet,
                    "type": type_att  # "normale" ou "ultime"
                })

            return {"nom": nom, "stats": stats, "attaques": attaques, "energie": 100, "vie": 100}

        p1 = parse_perso(perso1_data)
        p2 = parse_perso(perso2_data)

        # Détermine qui commence (mobilité + un peu d'aléatoire)
        p1_init = p1["stats"]["mobilité"] + random.randint(0, 10)
        p2_init = p2["stats"]["mobilité"] + random.randint(0, 10)
        tour_order = [p1, p2] if p1_init >= p2_init else [p2, p1]

        log = f"⚔️ **Combat entre {p1['nom']} et {p2['nom']} !**\n\n"

        for tour in range(5):  # 5 tours max
            for attaquant in tour_order:
                defenseur = p1 if attaquant == p2 else p2

                # Filtre les attaques possibles selon l'énergie
                possibles = [att for att in attaquant["attaques"] if att["cout"] <= attaquant["energie"]]
                if not possibles:
                    log += f"💤 {attaquant['nom']} est à court d'énergie et saute son tour.\n"
                    continue

                attaque = random.choice(possibles)
                att_stats = attaquant["stats"]
                def_stats = defenseur["stats"]

                # Calcul des dégâts : (attaque + force physique) - défense + pression spirituelle bonus
                base_degats = attaque["degats"]
                modificateur = (att_stats["attaque"] + att_stats["force"]) - def_stats["défense"]
                modificateur += att_stats["pression"] // 5
                modificateur = max(0, modificateur)  # pas de dégâts négatifs

                total_degats = base_degats + modificateur
                defenseur["vie"] -= total_degats
                attaquant["energie"] -= attaque["cout"]

                log += (
                    f"💥 {attaquant['nom']} utilise **{attaque['nom']}** "
                    f"({base_degats} + bonus, coût {attaque['cout']} énergie)\n"
                    f"➡️ {defenseur['nom']} perd {total_degats} PV (reste {defenseur['vie']} PV)\n\n"
                )

                if defenseur["vie"] <= 0:
                    log += f"🏆 **{attaquant['nom']} remporte le combat par KO !**"
                    await ctx.send(log)
                    return

        # Fin du combat si personne KO
        gagnant = p1 if p1["vie"] > p2["vie"] else p2
        log += f"🏁 Fin du combat. 🩸 **{p1['nom']}** : {p1['vie']} PV — **{p2['nom']}** : {p2['vie']} PV\n"
        log += f"🏆 **{gagnant['nom']} remporte le combat par avantage de vie !**"
        await ctx.send(log)

    except FileNotFoundError:
        await ctx.send("❌ Fichier `bleach_personnages.txt` introuvable.")
    except Exception as e:
        await ctx.send(f"⚠️ Une erreur est survenue : {e}")
combat_bleach.category = "Fun"


########## parti ##########
@bot.command(help="Génère un nom de parti politique aléatoire.")
async def parti(ctx):
    premiers_mots = [
        "Parti", "Mouvement", "Union", "Coalition", "Front", "Alliance", "Rassemblement", "Collectif", "Congrès",
        "Fédération", "Syndicat", "Bloc", "Cercle", "Comité", "Assemblée", "Association", "Organisation", "Ligue",
        "Confédération", "République", "Convention", "Société", "Force", "Ordre", "Phalange", "Campagne", "Brigade",
        "Réseau", "Unité", "Groupe", "Commission", "Délégation", "Section", "Faction", "Collectivité", "Conférence",
        "Coordination", "Plateforme", "Conseil", "Initiative", "Élan", "Accord", "Mission", "Engagement", "Forum",
        "Pacte", "Voix", "Chemin", "Sentier", "Marche", "Appel", "Serment", "Souffle", "Chant", "Idée", "Défi", "Table",
        "Union Civique", "Espoir", "Relève", "Cap", "Projet", "Symbole", "Nouveau Départ", "Avenir", "Perspective",
        "Éveil", "Nouvelle Voie", "Solidarité", "Impact", "Refondation", "Vision", "Transition", "Offensive", "Volonté",
        "Esprit", "Déclaration", "Position", "Engrenage", "Manifeste", "Pouvoir", "Regard", "Lueur", "Force Vive",
        "Fer de lance", "Boussole", "Moteur", "Cohorte", "Orientation", "Arc", "Barrage", "Voie", "Signal", "Ligne",
        "Feuille de route", "Clé", "Tournant", "Mur", "Barrière", "Bataillon"
    ]

    adjectifs = [
        "Populaire", "Républicain", "Social", "Démocratique", "National", "Écologique", "Progressiste", "Libéral",
        "Indépendant", "Patriotique", "Conservateur", "Radical", "Souverain", "Moderne", "Humaniste", "Révolutionnaire",
        "Communautaire", "Pluraliste", "Citoyen", "Socialiste", "Capitaliste", "Fédéral", "Populiste", "Égalitaire",
        "Patriotique", "Internationaliste", "Constitutionnel", "Pacifique", "Éthique", "Réformiste", "Sociétal", "Populaire",
        "Historique", "Économique", "Énergétique", "Technologique", "Agricole", "Industriel", "Cultural", "Social-démocrate",
        "Anti-corruption", "Nationaliste", "Libertaire", "Conservateur", "Dynamique", "Progressif", "Social-libéral",
        "Écologiste", "Féministe", "Pacifiste", "Militant", "Engagé", "Électoral", "Populaire", "Populiste", "Éthique",
        "Moderniste", "Constitutionnel", "Réformateur", "Soutenable", "Solidaire", "Intégrationniste", "Inclusif", "Responsable",
        "Social-national", "Républicain", "Libéral-démocrate", "Anti-autoritaire", "Social-républicain", "Participatif",
        "Populaire", "Social-démocrate", "Agrarien", "Communautaire", "Patriotique", "Autonome", "Populaire", "Écologiste",
        "Fédéraliste", "Historique", "Moderne", "Démocratique-populaire", "Populaire", "Conservateur", "Radical", "Populaire",
        "Souverainiste", "Révolutionnaire", "Internationaliste", "Social", "Égalitaire", "Populaire", "Libéral", "Démocrate"
    ]

    noms = [
        "Français", "Citoyen", "Révolutionnaire", "Travailleur", "Solidaire", "Indépendant", "Souverain", "Patriotique",
        "Réformateur", "Populaire", "Social", "Démocratique", "National", "Écologique", "Progressiste", "Libéral",
        "Égalitaire", "Fédéral", "Constitutionnel", "Pacifique", "Humaniste", "Radical", "Communautaire", "Pluraliste",
        "Militant", "Éthique", "Internationaliste", "Moderne", "Engagé", "Historique", "Populiste", "Agricole", "Industriel",
        "Technologique", "Socialiste", "Capitaliste", "Féministe", "Pacifiste", "Populaire", "Populiste", "Soutenable",
        "Solidaire", "Inclusif", "Responsable", "Nationaliste", "Libertaire", "Conservateur", "Réformiste", "Social-libéral",
        "Dynamique", "Écologiste", "Anti-corruption", "Participatif", "Autonome", "Fédéraliste", "Militant", "Révolutionnaire",
        "Humanitaire", "Communiste", "Social-démocrate", "Patriotique", "Populaire", "Progressiste", "Républicain",
        "Nationaliste", "Réformateur", "Social", "Populaire", "Radical", "Moderne", "Sociétal", "Pacifique", "Républicain",
        "Social", "Libéral", "Démocrate", "Souverain", "Patriotique", "Populaire", "Révolutionnaire", "National",
        "Écologique", "Indépendant", "Travailleur", "Socialiste", "Populaire", "Patriotique", "Libéral", "Réformiste",
        "Progressiste", "Humaniste", "Constitutionnel", "Pacifique", "Éthique", "Engagé", "Solidaire", "Égalitaire",
        "Social", "Populaire", "Citoyen", "Révolutionnaire"
    ]

    nom_parti = f"{random.choice(premiers_mots)} {random.choice(adjectifs)} {random.choice(noms)}"
    await ctx.send(f"🏛️ Voici un nom de parti politique : **{nom_parti}**")
parti.category = "Fun"



########## pendu ##########
@commands.command(name="pendu", help="Joue au pendu avec un mot aléatoire.")
async def pendu(ctx):
    await ctx.send("🕹️ Jeu du pendu lancé en DM...")

    # Récupération du mot aléatoire via API
    async with aiohttp.ClientSession() as session:
        async with session.get("https://trouve-mot.fr/api/random") as resp:
            if resp.status != 200:
                await ctx.send("❌ Impossible de récupérer un mot aléatoire.")
                return
            data = await resp.json()
            if not data:
                await ctx.send("❌ Aucun mot reçu de l'API.")
                return
            word = data[0]["word"].lower()

    # Variables de jeu
    guessed_letters = set()
    tries_left = 6
    display_word = ["_" if c.isalpha() else c for c in word]

    def format_word():
        return " ".join(display_word)

    def check(m):
        return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

    # Envoi du premier message dans les DM
    dm = await ctx.author.create_dm()
    await dm.send(f"🎮 Mot à deviner : {format_word()}\nTu as {tries_left} essais.\nPropose une lettre (envoie un message).")

    while tries_left > 0 and "_" in display_word:
        try:
            msg = await ctx.bot.wait_for("message", timeout=120.0, check=check)
        except asyncio.TimeoutError:
            await dm.send("⏰ Temps écoulé, partie terminée !")
            return

        guess = msg.content.lower()
        if len(guess) != 1 or not guess.isalpha():
            await dm.send("❌ Merci d'envoyer une seule lettre alphabétique.")
            continue

        if guess in guessed_letters:
            await dm.send(f"⚠️ Tu as déjà proposé la lettre `{guess}`.")
            continue

        guessed_letters.add(guess)

        if guess in word:
            for i, c in enumerate(word):
                if c == guess:
                    display_word[i] = guess
            await dm.send(f"✅ Bien joué !\n{format_word()}\nEssais restants : {tries_left}")
        else:
            tries_left -= 1
            await dm.send(f"❌ Lettre `{guess}` incorrecte.\n{format_word()}\nEssais restants : {tries_left}")

    if "_" not in display_word:
        await dm.send(f"🎉 Bravo ! Tu as trouvé le mot `{word}`.")
    else:
        await dm.send(f"💀 Partie terminée. Le mot était `{word}`.")

pendu.category = "Fun"




########## perso ##########
@bot.command(help="Découvre quel personnage de Bleach tu es (toujours le même pour toi).")
async def perso(ctx):
    user_id = ctx.author.id
    index = (user_id * 31 + 17) % len(bleach_characters)
    personnage = bleach_characters[index]
    await ctx.send(f"{ctx.author.mention}, tu es **{personnage}** ! (C'est ta destinée dans le monde de Bleach 🔥)")
perso.category = "Fun"


########## phrase ##########
@bot.command(name="phrase", help="Génère une phrase aléatoire à partir de listes de mots.")
async def phrase(ctx):
    try:
        with open("phrases_listes.txt", "r", encoding="utf-8") as f:
            content = f.read()

        # Sépare les 4 listes entre crochets par lignes vides
        listes = [ast.literal_eval(lst) for lst in content.strip().split('\n\n')]

        sujets, verbes, complements, adverbes = listes

        phrase_generee = f"{random.choice(sujets)} {random.choice(verbes)} {random.choice(complements)} {random.choice(adverbes)}."
        await ctx.send(phrase_generee)

    except FileNotFoundError:
        await ctx.send("❌ Fichier `phrases_listes.txt` introuvable.")
    except Exception as e:
        await ctx.send(f"⚠️ Une erreur est survenue : {e}")

phrase.category = "Fun"


########## 🪙 Pile ou face ##########
@bot.command(help="Lance une pièce : pile ou face.")
async def pof(ctx):
    resultat = random.choice(["🪙 Pile !", "🪙 Face !"])
    await ctx.send(resultat)
pof.category = "Fun"



########## recommande ##########
@bot.command(help="commande + solo ou multi. Le bot te recommande un jeu.")
async def recommande(ctx, type_jeu: str = None):
    import random

    if type_jeu is None:
        await ctx.send("Il faut ajouter l'argument 'solo' ou l'argument 'multi' à la commande pour que le bot recommande un jeu solo ou multijoueur.")
        return

    type_jeu = type_jeu.lower()

    try:
        with open("jeux.txt", "r", encoding="utf-8") as f:
            lignes = f.readlines()
    except FileNotFoundError:
        await ctx.send("❌ Fichier `jeux.txt` introuvable.")
        return

    jeux_solo = []
    jeux_multi = []
    section = None

    for ligne in lignes:
        ligne = ligne.strip()
        if ligne == "[SOLO]":
            section = "solo"
            continue
        elif ligne == "[MULTI]":
            section = "multi"
            continue
        elif not ligne or ligne.startswith("#"):
            continue  # ignorer les lignes vides ou commentaires

        if section == "solo":
            jeux_solo.append(ligne)
        elif section == "multi":
            jeux_multi.append(ligne)

    if type_jeu == "solo":
        if jeux_solo:
            jeu = random.choice(jeux_solo)
            await ctx.send(f"🎮 Jeu **solo** recommandé : **{jeu}**")
        else:
            await ctx.send("⚠️ Aucun jeu solo trouvé dans le fichier.")
    elif type_jeu == "multi":
        if jeux_multi:
            jeu = random.choice(jeux_multi)
            await ctx.send(f"🎮 Jeu **multijoueur** recommandé : **{jeu}**")
        else:
            await ctx.send("⚠️ Aucun jeu multijoueur trouvé dans le fichier.")
    else:
        await ctx.send("Il faut ajouter l'argument 'solo' ou l'argument 'multi' à la commande pour que le bot recommande un jeu solo ou multijoueur.")


recommande.category = "Fun"



#############################
########## admin ##########
#############################

########## 🔧 Préfixe (admin uniquement) ##########
@bot.command(help="Affiche ou change le préfixe du bot (admin uniquement).")
@commands.has_permissions(administrator=True)
async def prefixe(ctx, nouveau: str = None):
    if not os.path.exists(".env"):
        await ctx.send("❌ Le fichier `.env` est introuvable.")
        return

    if nouveau is None:
        prefix = get_prefix(bot, ctx.message)
        await ctx.send(f"ℹ️ Le préfixe actuel est : `{prefix}`")
    else:
        with open(".env", "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(".env", "w", encoding="utf-8") as f:
            prefix_updated = False
            for line in lines:
                if line.startswith("COMMAND_PREFIX="):
                    f.write(f"COMMAND_PREFIX={nouveau}\n")
                    prefix_updated = True
                else:
                    f.write(line)
            if not prefix_updated:
                f.write(f"COMMAND_PREFIX={nouveau}\n")

        await ctx.send(f"✅ Préfixe changé en : `{nouveau}`. Redémarre le bot pour que le changement prenne effet.")
prefixe.category = "Admin"

# Debug infos
print("Dossier de travail actuel :", os.getcwd())
print("Fichiers dans le dossier :", os.listdir())

# Démarre le serveur web pour le keep-alive
keep_alive()

# Lancer le bot
bot.run(TOKEN)
