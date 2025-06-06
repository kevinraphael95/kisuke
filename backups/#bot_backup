# ──────────────────────────────────────────────────────────────
# 🟢 Serveur Keep-Alive (Render)
# ──────────────────────────────────────────────────────────────
from keep_alive import keep_alive

# ──────────────────────────────────────────────────────────────
# 📦 Modules standards
# ──────────────────────────────────────────────────────────────
import os
import json
import uuid
import random
from datetime import datetime, timezone
import asyncio  # ✅ Nécessaire pour lancer le bot de manière asynchrone

# ──────────────────────────────────────────────────────────────
# 📦 Modules tiers
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from dotenv import load_dotenv
from dateutil import parser

# ──────────────────────────────────────────────────────────────
# 📦 Modules internes
# ──────────────────────────────────────────────────────────────
from supabase_client import supabase

# ──────────────────────────────────────────────────────────────
# 🔧 Initialisation de l’environnement
# ──────────────────────────────────────────────────────────────

# Se placer dans le dossier du script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Charger les variables d’environnement (.env)
load_dotenv()

# Clés importantes
TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
INSTANCE_ID = str(uuid.uuid4())

# Enregistrer cette instance
with open("instance_id.txt", "w") as f:
    f.write(INSTANCE_ID)

# Fonction pour le préfixe dynamique (ici statique)
def get_prefix(bot, message):
    return COMMAND_PREFIX

# ──────────────────────────────────────────────────────────────
# ⚙️ Intents & Création du bot
# ──────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)
bot.is_main_instance = False

# ──────────────────────────────────────────────────────────────
# 📁 JSON : on charge les réponses depuis le dossier data/
# ──────────────────────────────────────────────────────────────
with open("data/reponses.json", encoding="utf-8") as f:
    REPONSES = json.load(f)

GIFS_FOLDER = "gifs"

# ──────────────────────────────────────────────────────────────
# 🔌 Chargement dynamique des commandes depuis /commands/*
# ──────────────────────────────────────────────────────────────
async def load_commands():
    for category in os.listdir("commands"):
        cat_path = os.path.join("commands", category)
        if os.path.isdir(cat_path):
            for filename in os.listdir(cat_path):
                if filename.endswith(".py"):
                    path = f"commands.{category}.{filename[:-3]}"
                    try:
                        await bot.load_extension(path)  # ✅ async / await
                        print(f"✅ Loaded {path}")
                    except Exception as e:
                        print(f"❌ Failed to load {path}: {e}")

# ──────────────────────────────────────────────────────────────
# 🔔 On Ready : présence + verrouillage de l’instance
# ──────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user.name}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Bleach"))

    now = datetime.now(timezone.utc).isoformat()

    print("💣 Suppression de tout verrou précédent...")
    supabase.table("bot_lock").delete().eq("id", "reiatsu_lock").execute()

    print(f"🔐 Prise de verrou par cette instance : {INSTANCE_ID}")
    supabase.table("bot_lock").insert({
        "id": "reiatsu_lock",
        "instance_id": INSTANCE_ID,
        "updated_at": now
    }).execute()

    bot.is_main_instance = True
    print(f"✅ Instance principale active : {INSTANCE_ID}")

    # ⬇️ Ajout du spawner
    await bot.load_extension("commands.reiatsu.spawner")
    print("✅ Spawner Reiatsu chargé.")


# ──────────────────────────────────────────────────────────────
# 📩 Message reçu : réagir aux mots-clés et lancer les commandes
# ──────────────────────────────────────────────────────────────
@bot.event
async def on_message(message):
    # Vérifie si c’est bien l’instance principale
    lock = supabase.table("bot_lock").select("instance_id").eq("id", "reiatsu_lock").execute()
    if lock.data and lock.data[0]["instance_id"] != INSTANCE_ID:
        return

    if message.author.bot:
        return

    contenu = message.content.lower()

    # Réaction auto via mot-clé
    for mot in REPONSES:
        if mot in contenu:
            texte = random.choice(REPONSES[mot])
            dossier_gif = os.path.join(GIFS_FOLDER, mot)
            if os.path.exists(dossier_gif):
                gifs = [f for f in os.listdir(dossier_gif) if f.endswith((".gif", ".mp4"))]
                if gifs:
                    chemin = os.path.join(dossier_gif, random.choice(gifs))
                    await message.channel.send(content=texte, file=discord.File(chemin))
                    return
            await message.channel.send(texte)
            return

    # ✅ Nouveau bloc pour réponse si bot est mentionné
    if (
        bot.user in message.mentions
        and len(message.mentions) == 1
        and message.content.strip().startswith(f"<@{bot.user.id}")
    ):
        prefix = get_prefix(bot, message)

        embed = discord.Embed(
            title="Bleach Bot",
            description="Bonjour, je suis un bot basé sur l'univers de **Bleach** !\n"
                        f"Mon préfixe est : `{prefix}`\n\n"
                        f"📜 Tape `{prefix}help` pour voir toutes les commandes disponibles. (cassé)\n"
                        f"🛠️ Tape `{prefix}commandes` pour voir les commandes. (meh)\n"
                        f"ℹ️ Tape `{prefix}info` pour avoir plus d'infos sur l''état du bot.",
            color=discord.Color.orange()
        )
        if bot.user.avatar:
            embed.set_thumbnail(url=bot.user.avatar.url)
        embed.set_footer(text="Zangetsu veille sur toi.")
        await message.channel.send(embed=embed)
        return

    # Exécution des commandes classiques
    await bot.process_commands(message)

# ──────────────────────────────────────────────────────────────
# ❗ Gestion des erreurs de commandes
# ──────────────────────────────────────────────────────────────
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry = round(error.retry_after, 1)
        await ctx.send(f"⏳ Cette commande est en cooldown. Réessaie dans `{retry}` secondes.")
    
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Tu n'as pas les permissions pour cette commande.")
    
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Il manque un argument à cette commande.")
    
    elif isinstance(error, commands.CommandNotFound):
        return  # ignore les commandes non reconnues

    else:
        # 🔧 En dev : utile pour voir les autres erreurs
        raise error



# ──────────────────────────────────────────────────────────────
# 🚀 Lancement
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    keep_alive()

    async def start():
        await load_commands()
        await bot.start(TOKEN)

    asyncio.run(start())
