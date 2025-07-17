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

    # ⚠️ Charge aussi le Cog heartbeat qui lance la tâche automatiquement
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
                    await safe_send(message.channel, content=texte, file=discord.File(chemin))
                    return
            await safe_send(message.channel, content=texte)
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
                        f"📜 Tape `{prefix}help` pour voir toutes les commandes disponibles.",
            color=discord.Color.orange()
        )
        if bot.user.avatar:
            embed.set_thumbnail(url=bot.user.avatar.url)
        embed.set_footer(text="Zangetsu veille sur toi.")
        await safe_send(message.channel, embed=embed)
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
        await safe_send(ctx.channel, f"⏳ Cette commande est en cooldown. Réessaie dans `{retry}` secondes.")
    
    elif isinstance(error, commands.MissingPermissions):
        await safe_send(ctx.channel, "❌ Tu n'as pas les permissions pour cette commande.")
    
    elif isinstance(error, commands.MissingRequiredArgument):
        await safe_send(ctx.channel, "⚠️ Il manque un argument à cette commande.")
    
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
