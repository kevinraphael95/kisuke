# ────────────────────────────────────────────────────────────────────────────────
# 📌 bot.py — Script principal du bot Discord
# Objectif : Initialisation, gestion des commandes, événements et gestion centralisée des erreurs et cooldowns
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 🟢 Serveur Keep-Alive (Render)
# ──────────────────────────────────────────────────────────────
from tasks.keep_alive import keep_alive

# ──────────────────────────────────────────────────────────────
# 📦 Modules standards
# ──────────────────────────────────────────────────────────────
import os
import uuid
import asyncio
from datetime import datetime, timezone

# ──────────────────────────────────────────────────────────────
# 📦 Modules tiers
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────
# 📦 Modules internes
# ──────────────────────────────────────────────────────────────
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ──────────────────────────────────────────────────────────────
# 🔧 Initialisation
# ──────────────────────────────────────────────────────────────
os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
INSTANCE_ID = str(uuid.uuid4())

with open("instance_id.txt", "w") as f:
    f.write(INSTANCE_ID)

def get_prefix(bot, message):
    return COMMAND_PREFIX

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)
bot.INSTANCE_ID = INSTANCE_ID
bot.supabase = supabase
bot.is_main_instance = False

# ──────────────────────────────────────────────────────────────
# 🔌 Chargement dynamique des extensions
# ──────────────────────────────────────────────────────────────
async def load_extensions():
    """Charge toutes les commandes et tâches."""
    # Chargement des commandes
    for root, dirs, files in os.walk("commands"):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                path = os.path.relpath(os.path.join(root, file), ".").replace(os.path.sep, ".").replace(".py", "")
                try:
                    if path in bot.extensions:
                        await bot.unload_extension(path)
                    await bot.load_extension(path)
                    print(f"✅ Loaded {path}")
                except Exception as e:
                    print(f"❌ Failed to load {path}: {e}")

    # Chargement des tâches
    for task in ["tasks.heartbeat", "tasks.reiatsu_spawner"]:
        try:
            if task in bot.extensions:
                await bot.unload_extension(task)
            await bot.load_extension(task)
            print(f"✅ Loaded {task}")
        except Exception as e:
            print(f"❌ Failed to load {task}: {e}")

# ──────────────────────────────────────────────────────────────
# 🔔 Événement on_ready
# ──────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Bleach"))

    # Gestion verrou Supabase
    now = datetime.now(timezone.utc).isoformat()
    try:
        supabase.table("bot_lock").delete().eq("id", "main_lock").execute()
        supabase.table("bot_lock").insert({
            "id": "main_lock",
            "instance_id": INSTANCE_ID,
            "updated_at": now
        }).execute()
        bot.is_main_instance = True
        print(f"✅ Instance principale active : {INSTANCE_ID}")
    except Exception as e:
        print(f"⚠️ Vérification du verrou Supabase échouée : {e}")

    # Synchronisation slash commands **après avoir chargé toutes les extensions**
    try:
        await bot.tree.sync()
        print("✅ Slash commands synchronisées")
    except Exception as e:
        print(f"⚠️ Impossible de synchroniser les slash commands : {e}")

# ──────────────────────────────────────────────────────────────
# 📩 Événement on_message
# ──────────────────────────────────────────────────────────────
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # Vérification du verrou Supabase
    try:
        lock = supabase.table("bot_lock").select("instance_id").eq("id", "main_lock").execute()
        if lock.data and lock.data[0]["instance_id"] != INSTANCE_ID:
            return
    except Exception as e:
        print(f"⚠️ Vérification du verrou Supabase échouée : {e}")

    prefix = get_prefix(bot, message)
    if message.content.strip() in [f"<@{bot.user.id}>", f"<@!{bot.user.id}>"]:
        await safe_send(message.channel, f"👋 Salut {message.author.mention} ! Utilise `{prefix}help` pour voir les commandes.")
        return

    if message.content.startswith(prefix):
        await bot.process_commands(message)

# ──────────────────────────────────────────────────────────────
# ⚠️ Gestion centralisée des erreurs
# ──────────────────────────────────────────────────────────────
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await safe_send(ctx.channel, f"⏳ Patiente {error.retry_after:.1f}s avant de réutiliser cette commande.")
    elif isinstance(error, commands.MissingPermissions):
        await safe_send(ctx.channel, "❌ Tu n'as pas la permission d'utiliser cette commande.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"[ERREUR COMMANDE] {ctx.command}: {error}")
        await safe_send(ctx.channel, "❌ Une erreur est survenue.")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        await safe_respond(interaction, f"⏳ Patiente {error.retry_after:.1f}s avant de réutiliser cette commande.", ephemeral=True)
    elif isinstance(error, app_commands.MissingPermissions):
        await safe_respond(interaction, "❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
    else:
        print(f"[ERREUR SLASH] {interaction.command}: {error}")
        await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    try:
        await bot.tree.on_interaction(interaction)
    except Exception as e:
        print(f"[ERREUR INTERACTION] {e}")
        try:
            if interaction.response.is_done():
                await interaction.followup.send("❌ Une erreur est survenue.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Une erreur est survenue.", ephemeral=True)
        except Exception:
            pass

# ──────────────────────────────────────────────────────────────
# 🚀 Lancement du bot
# ──────────────────────────────────────────────────────────────
async def main():
    await load_extensions()
    await bot.start(TOKEN)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
