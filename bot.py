# ──────────────────────────────────────────────────────────────
# 🟢 Serveur Keep-Alive (Render)
# ──────────────────────────────────────────────────────────────
from tasks.keep_alive import keep_alive

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
from utils.discord_utils import safe_send, safe_edit, safe_respond  # <-- import safe utils

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
bot.INSTANCE_ID = INSTANCE_ID      # 🔁 Ajout pour heartbeat.py
bot.supabase = supabase            # 🔁 Ajout pour heartbeat.py

# ──────────────────────────────────────────────────────────────
# 📁 JSON : on charge les réponses depuis le dossier data/
# ──────────────────────────────────────────────────────────────
with open("data/reponses.json", encoding="utf-8") as f:
    REPONSES = json.load(f)

GIFS_FOLDER = "data/gifs"

# ──────────────────────────────────────────────────────────────
# 🔌 Chargement dynamique des commandes depuis /commands/*
# ──────────────────────────────────────────────────────────────
async def load_commands():
    for root, dirs, files in os.walk("commands"):
        for file in files:
            if file.endswith(".py"):
                # Convertir "commands/general/help.py" → "commands.general.help"
                relative_path = os.path.relpath(os.path.join(root, file), ".")
                module_path = relative_path.replace(os.path.sep, ".").replace(".py", "")
                try:
                    # D'abord tenter de décharger si déjà chargé (optionnel)
                    if module_path in bot.extensions:
                        await bot.unload_extension(module_path)
                    await bot.load_extension(module_path)
                    print(f"✅ Loaded {module_path}")
                except Exception as e:
                    print(f"❌ Failed to load {module_path}: {e}")

    # Charger les autres cogs (hors commands/)
    try:
        await bot.load_extension("tasks.heartbeat")
        print("✅ Loaded tasks.heartbeat")
    except Exception as e:
        print(f"❌ Failed to load tasks.heartbeat: {e}")


# ──────────────────────────────────────────────────────────────
# 🔔 On Ready : présence + verrouillage de l’instance
# ──────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user.name}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Bleach"))

    now = datetime.now(timezone.utc).isoformat()

    try:
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
        await bot.load_extension("tasks.reiatsu_spawner")
        print("✅ Spawner Reiatsu chargé.")
    except Exception as e:
        print(f"⚠️ Impossible de se connecter à Supabase : {e}")
        print("🔓 Aucune gestion de verrou — le bot démarre quand même.")

# ──────────────────────────────────────────────────────────────
# 📩 Message reçu : réagir aux mots-clés et lancer les commandes
# ──────────────────────────────────────────────────────────────
@bot.event
async def on_message(message):
    # Vérifie si c’est bien l’instance principale
    try:
        lock = supabase.table("bot_lock").select("instance_id").eq("id", "reiatsu_lock").execute()
        if lock.data and lock.data[0]["instance_id"] != INSTANCE_ID:
            return
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification du verrou Supabase : {e}")
        # Si Supabase échoue, on laisse passer quand même

    # Ignore les messages du bot ou d’autres bots
    if message.author.bot:
        return

    # Parfois les préfixes sont plusieurs, ici fixe
    prefix = get_prefix(bot, message)
    if not message.content.startswith(prefix):
        # On peut éventuellement faire une réponse aux mots clés ici
        return

    await bot.process_commands(message)

# ──────────────────────────────────────────────────────────────
# 🚀 Lancement du bot
# ──────────────────────────────────────────────────────────────
async def main():
    await load_commands()
    await bot.start(TOKEN)

if __name__ == "__main__":
    keep_alive()  # Pour Render.com par exemple
    asyncio.run(main())
