# ────────────────────────────────────────────────────────────────────────────────
# 📌 bot.py — Script principal du bot Discord
# Objectif : Initialisation, gestion des commandes, événements et gestion centralisée des erreurs
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
import json
import uuid
import asyncio
from datetime import datetime, timezone

# ──────────────────────────────────────────────────────────────
# 📦 Modules tiers
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from dotenv import load_dotenv

# ──────────────────────────────────────────────────────────────
# 📦 Modules internes
# ──────────────────────────────────────────────────────────────
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_edit, safe_respond  # <-- fonctions "safe"

# ──────────────────────────────────────────────────────────────
# 🔧 Initialisation de l’environnement
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
bot.INSTANCE_ID = INSTANCE_ID
bot.supabase = supabase

# ──────────────────────────────────────────────────────────────
# 🔌 Chargement dynamique des commandes
# ──────────────────────────────────────────────────────────────
async def load_commands():
    for root, dirs, files in os.walk("commands"):
        for file in files:
            if file.endswith(".py"):
                relative_path = os.path.relpath(os.path.join(root, file), ".")
                module_path = relative_path.replace(os.path.sep, ".").replace(".py", "")
                try:
                    if module_path in bot.extensions:
                        await bot.unload_extension(module_path)
                    await bot.load_extension(module_path)
                    print(f"✅ Loaded {module_path}")
                except Exception as e:
                    print(f"❌ Failed to load {module_path}: {e}")

    try:
        await bot.load_extension("tasks.heartbeat")
        print("✅ Loaded tasks.heartbeat")
    except Exception as e:
        print(f"❌ Failed to load tasks.heartbeat: {e}")

# ──────────────────────────────────────────────────────────────
# 🔔 Événement on_ready : présence + verrouillage
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

        # Chargement du spawner Reiatsu
        await bot.load_extension("tasks.reiatsu_spawner")
        print("✅ Spawner Reiatsu chargé.")

        # synchronisation des commandes slash
        await bot.tree.sync()
        print("✅ Slash commands synchronisées")
    except Exception as e:
        print(f"⚠️ Impossible de se connecter à Supabase : {e}")
        print("🔓 Aucune gestion de verrou — le bot démarre quand même.")

# ──────────────────────────────────────────────────────────────
# 📩 Événement on_message : gestion du verrou + commandes
# ──────────────────────────────────────────────────────────────
@bot.event
async def on_message(message):
    try:
        lock = supabase.table("bot_lock").select("instance_id").eq("id", "reiatsu_lock").execute()
        if lock.data and lock.data[0]["instance_id"] != INSTANCE_ID:
            return
    except Exception as e:
        print(f"⚠️ Erreur lors de la vérification du verrou Supabase : {e}")
        # On continue quand même

    if message.author.bot:
        return

    prefix = get_prefix(bot, message)

    # ✅ Répondre à la mention directe du bot
    if message.content.strip() in [f"<@{bot.user.id}>", f"<@!{bot.user.id}>"]:
        await safe_send(message.channel, f"👋 Salut {message.author.mention} ! Utilise `{prefix}help` pour voir mes commandes.")
        return

    if not message.content.startswith(prefix):
        return

    await bot.process_commands(message)

# ──────────────────────────────────────────────────────────────
# ⚠️ Gestion centralisée des erreurs et cooldowns
# ──────────────────────────────────────────────────────────────
@bot.event
async def on_command_error(ctx, error):
    """Gestion pour commandes préfixées"""
    if isinstance(error, commands.CommandOnCooldown):
        await safe_send(ctx.channel, f"⏳ Patiente {error.retry_after:.1f}s avant de réutiliser cette commande.")
    elif isinstance(error, commands.MissingPermissions):
        await safe_send(ctx.channel, "❌ Tu n'as pas la permission d'utiliser cette commande.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"[ERREUR COMMANDE] {ctx.command}: {error}")
        await safe_send(ctx.channel, "❌ Une erreur est survenue lors de l'exécution de la commande.")

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    """Gestion pour commandes slash"""
    if isinstance(error, app_commands.CommandOnCooldown):
        await safe_respond(interaction, f"⏳ Patiente {error.retry_after:.1f}s avant de réutiliser cette commande.", ephemeral=True)
    elif isinstance(error, app_commands.MissingPermissions):
        await safe_respond(interaction, "❌ Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
    else:
        print(f"[ERREUR SLASH] {interaction.command}: {error}")
        await safe_respond(interaction, "❌ Une erreur est survenue lors de l'exécution de la commande.", ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    """Gestion pour boutons, menus et modals"""
    try:
        await bot.tree.on_interaction(interaction)  # traite l'interaction normalement
    except Exception as e:
        print(f"[ERREUR INTERACTION] {e}")
        try:
            if interaction.response.is_done():
                await interaction.followup.send("❌ Une erreur est survenue.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Une erreur est survenue.", ephemeral=True)
        except Exception:
            pass  # Évite un crash si Discord refuse la réponse

# ──────────────────────────────────────────────────────────────
# 🚀 Lancement du bot
# ──────────────────────────────────────────────────────────────
async def main():
    await load_commands()
    await bot.start(TOKEN)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
