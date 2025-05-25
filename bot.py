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

# ──────────────────────────────────────────────────────────────
# 📩 Message reçu : réagir aux mots-clés et lancer les commandes
# ──────────────────────────────────────────────────────────────
@bot.event
async def on_message(message):
    lock = supabase.table("bot_lock").select("instance_id").eq("id", "reiatsu_lock").execute()
    if lock.data and lock.data[0]["instance_id"] != INSTANCE_ID:
        return

    if message.author.bot:
        return

    contenu = message.content.lower()

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

    await bot.process_commands(message)

# ──────────────────────────────────────────────────────────────
# 🚀 Lancement
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    keep_alive()

    async def start():
        await load_commands()
        await bot.start(TOKEN)

    asyncio.run(start())
