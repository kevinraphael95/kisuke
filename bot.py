# Serveur Keep-Alive pour hébergement (Replit ou autres)
from keep_alive import keep_alive

# Modules standards
import os
import io
import ast
import asyncio
import json
import hashlib
import random
import time
import uuid

# Modules tiers
import aiohttp
import discord
from discord.ext import commands, tasks
from discord.ui import View, Select, Button
from discord import SelectOption, Interaction, Embed
from dotenv import load_dotenv
from dateutil import parser
from datetime import datetime



# Modules internes
from supabase_client import supabase  # Fichier Supabase perso

# ─────────────────────────────────────────────
# 🔧 Initialisation de l'environnement
# ─────────────────────────────────────────────

# Répertoire de travail
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Charger les variables d’environnement (.env)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
INVITE_URL = os.getenv("INVITE_URL")
app_id = os.getenv("DISCORD_APP_ID")

# ID unique de cette instance du bot
INSTANCE_ID = str(uuid.uuid4())  # 🔒 Sert à éviter les doubles exécutions Render

# Charger les réponses préconfigurées
REPONSES_JSON_PATH = "reponses.json"
with open(REPONSES_JSON_PATH, encoding="utf-8") as f:
    REPONSES = json.load(f)

# Dossier pour les fichiers gifs
GIFS_FOLDER = "gifs"

# ─────────────────────────────────────────────
# ⚙️ Configuration du bot
# ─────────────────────────────────────────────

# Intents (droits d'accès aux événements Discord)
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

# Préfixe dynamique
def get_prefix(bot, message):
    return COMMAND_PREFIX

# Création du bot
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)
bot.is_main_instance = False  # ✅ Ajoute cette ligne


# ─────────────────────────────────────────────
# 🔔 Événements du bot
# ─────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅ Connecté en tant que {bot.user.name}")
    activity = discord.Activity(type=discord.ActivityType.watching, name="Bleach")
    await bot.change_presence(activity=activity)

    # Vérifie ou prend le verrou
    now = datetime.utcnow().isoformat()
    lock = supabase.table("bot_lock").select("*").eq("id", "reiatsu_lock").execute()

    should_start = False

    if not lock.data:
        should_start = True
    else:
        existing = lock.data[0]
        updated_at = parser.parse(existing["updated_at"]).timestamp()
        age = time.time() - updated_at

        # Si vieux verrou (ex: instance morte), on le reprend
        if age > 60:  # ⚠️ ici 60 secondes (tu peux mettre 30 ou 300)
            should_start = True
        else:
            # Même instance ? → on continue
            if existing.get("instance_id") == INSTANCE_ID:
                should_start = True
            else:
                print("⛔ Une autre instance est active. Ce bot reste passif.")
                bot.is_main_instance = False
                return

    if should_start:
        supabase.table("bot_lock").upsert({
            "id": "reiatsu_lock",
            "instance_id": INSTANCE_ID,
            "updated_at": now
        }).execute()

        bot.is_main_instance = True
        print(f"🔓 Verrou pris par cette instance ({INSTANCE_ID})")

        if not hasattr(bot, "reiatsu_spawner"):
            bot.reiatsu_spawner = ReiatsuSpawner(bot)

        bot.reiatsu_spawner.resume()
        print("▶️ Spawn Reiatsu activé.")




# ─────────────────────────────────────────────
# on message
# ─────────────────────────────────────────────


@bot.event
async def on_message(message):
    if not getattr(bot, "is_main_instance", False):
        return  # Ignore si ce n’est pas l’instance principale

    if message.author.bot:
        return

    contenu = message.content.lower()

    # Répondre à la mention du bot
    if (
        bot.user in message.mentions
        and len(message.mentions) == 1
        and message.content.strip().startswith(f"<@")
    ):
        prefix = get_prefix(bot, message)

        embed = discord.Embed(
            title="Bleach Bot",
            description="Bonjour, je suis un bot basé sur l'univers de **Bleach** !\n"
                        f"Mon préfixe est : `{prefix}`\n\n"
                        f"📜 Tape `{prefix}help` pour voir toutes les commandes disponibles.",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else discord.Embed.Empty)
        embed.set_footer(text="Zangetsu veille sur toi.")
        await message.channel.send(embed=embed)
        return

    # Réponse aux mots-clés (comme "bleach", "bankai", etc.)
    for mot in REPONSES:
        if mot in contenu:
            textes = REPONSES[mot]
            texte = random.choice(textes)

            dossier_gif = os.path.join(GIFS_FOLDER, mot)
            if os.path.exists(dossier_gif):
                gifs_dispo = [f for f in os.listdir(dossier_gif) if f.endswith((".gif", ".mp4"))]
                if gifs_dispo:
                    gif_choisi = random.choice(gifs_dispo)
                    chemin = os.path.join(dossier_gif, gif_choisi)
                    file = discord.File(chemin, filename=gif_choisi)
                    await message.channel.send(content=texte, file=file)
                    break
            # Si pas de GIF, envoyer seulement le texte
            await message.channel.send(texte)
            break

    # Exécuter les commandes (si !commande ou préfixe)
    await bot.process_commands(message)




# ─────────────────────────────────────────────
# commandes
# ─────────────────────────────────────────────

        
# ─────────────────────────────────────────────
# reiatsu
# ─────────────────────────────────────────────



# test reiatsu
# ─────────────────────────────────────────────

# test reiatsu
# ─────────────────────────────────────────────

# Salon où le Reiatsu spawn
async def get_reiatsu_channel(bot, guild_id):
    data = supabase.table("reiatsu_config").select("channel_id").eq("guild_id", str(guild_id)).execute()
    if data.data:
        channel_id = int(data.data[0]["channel_id"])
        return bot.get_channel(channel_id)
    return None


class ReiatsuSpawner:
    def __init__(self, bot):
        self.bot = bot
        self.spawn_loop = self.spawn_loop_body

    @tasks.loop(seconds=60)
    async def spawn_loop_body(self):
        await self.bot.wait_until_ready()
        now = int(time.time())

        # On récupère toutes les configurations
        configs = supabase.table("reiatsu_config") \
            .select("guild_id", "channel_id", "last_spawn_at", "delay_minutes") \
            .execute()

        for conf in configs.data:
            guild_id = conf["guild_id"]
            channel_id = conf.get("channel_id")
            if not channel_id:
                continue

            last_spawn_str = conf.get("last_spawn_at")
            delay = conf.get("delay_minutes") or 1800

            # Détermine s'il faut spawner
            if not last_spawn_str:
                should_spawn = True
            else:
                last_spawn = parser.parse(last_spawn_str).timestamp()
                should_spawn = now - int(last_spawn) >= int(delay)

            if not should_spawn:
                continue  # Pas encore le moment

            # ✅ Spawn Reiatsu
            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                continue

            embed = discord.Embed(
                title="💠 Un Reiatsu sauvage apparaît !",
                description="Cliquez sur la réaction 💠 pour l'absorber.",
                color=discord.Color.purple()
            )
            message = await channel.send(embed=embed)
            await message.add_reaction("💠")

            def check(reaction, user):
                return (
                    reaction.message.id == message.id and
                    str(reaction.emoji) == "💠" and
                    not user.bot
                )

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=10800.0, check=check)

                data = supabase.table("reiatsu").select("id", "points").eq("user_id", str(user.id)).execute()
                if data.data:
                    current = data.data[0]["points"]
                    supabase.table("reiatsu").update({"points": current + 1}).eq("user_id", str(user.id)).execute()
                else:
                    supabase.table("reiatsu").insert({
                        "user_id": str(user.id),
                        "username": str(user.name),
                        "points": 1
                    }).execute()

                await channel.send(f"{user.mention} a absorbé le Reiatsu et gagné **+1** point !")

            except asyncio.TimeoutError:
                await channel.send("Le Reiatsu s'est dissipé dans l'air... personne ne l'a absorbé.")

            # 🔄 Met à jour le prochain spawn
            new_delay = random.randint(1800, 5400)
            supabase.table("reiatsu_config").update({
                "last_spawn_at": datetime.utcnow().isoformat(),
                "delay_minutes": new_delay
            }).eq("guild_id", guild_id).execute()

    def pause(self):
        if self.spawn_loop.is_running():
            self.spawn_loop.cancel()

    def resume(self):
        if not self.spawn_loop.is_running():
            self.spawn_loop.start()




# setreiatsu
# ─────────────────────────────────────────────

@bot.command(name="setreiatsu", aliases=["setrts"])
@commands.has_permissions(administrator=True)
async def setreiatsu(ctx):
    channel_id = ctx.channel.id
    guild_id = ctx.guild.id

    # Vérifie si une config existe déjà
    data = supabase.table("reiatsu_config").select("id").eq("guild_id", str(guild_id)).execute()
    if data.data:
        supabase.table("reiatsu_config").update({"channel_id": str(channel_id)}).eq("guild_id", str(guild_id)).execute()
    else:
        supabase.table("reiatsu_config").insert({
            "guild_id": str(guild_id),
            "channel_id": str(channel_id)
        }).execute()

    await ctx.send(f"💠 Le salon actuel ({ctx.channel.mention}) est maintenant le salon Reiatsu.")
setreiatsu.category = "Reiatsu"




# unsetreiatsu
# ─────────────────────────────────────────────

@bot.command(name="unsetreiatsu", aliases=["unsetrts"])
@commands.has_permissions(administrator=True)
async def unsetreiatsu(ctx):
    """Supprime le salon configuré pour le spawn de Reiatsu."""
    guild_id = str(ctx.guild.id)

    data = supabase.table("reiatsu_config").select("id").eq("guild_id", guild_id).execute()
    if data.data:
        supabase.table("reiatsu_config").delete().eq("guild_id", guild_id).execute()
        await ctx.send("🗑️ Le salon Reiatsu a été supprimé de la configuration.")
    else:
        await ctx.send("❌ Aucun salon Reiatsu n'était configuré pour ce serveur.")
unsetreiatsu.category = "Reiatsu"



# reiatsu
# ─────────────────────────────────────────────

@bot.command(name="reiatsu", aliases=["rts"])
async def reiatsu(ctx, member: discord.Member = None):
    """Affiche le score de Reiatsu d'un membre (ou soi-même)."""
    user = member or ctx.author
    data = supabase.table("reiatsu").select("points").eq("user_id", str(user.id)).execute()

    if data.data:
        points = data.data[0]["points"]
    else:
        points = 0

    await ctx.send(f"💠 {user.mention} a **{points}** points de Reiatsu.")
reiatsu.category = "Reiatsu"

# addreiatsu
# ─────────────────────────────────────────────

@bot.command(name="addreiatsu", aliases=["rts+"])
@commands.has_permissions(administrator=True)
async def addreiatsu(ctx, member: discord.Member, amount: int):
    """Ajoute des points de Reiatsu à un membre."""
    if amount <= 0:
        await ctx.send("❌ Le montant doit être positif.")
        return

    data = supabase.table("reiatsu").select("points").eq("user_id", str(member.id)).execute()

    if data.data:
        current = data.data[0]["points"]
        supabase.table("reiatsu").update({"points": current + amount}).eq("user_id", str(member.id)).execute()
    else:
        supabase.table("reiatsu").insert({
            "user_id": str(member.id),
            "username": member.name,
            "points": amount
        }).execute()

    await ctx.send(f"✅ Ajouté **+{amount}** points de Reiatsu à {member.mention}.")
addreiatsu.category = "Reiatsu"


# delreiatsu
# ─────────────────────────────────────────────

@bot.command(name="delreiatsu", aliases=["rts-"])
@commands.has_permissions(administrator=True)
async def delreiatsu(ctx, member: discord.Member, amount: int):
    """Retire des points de Reiatsu à un membre."""
    if amount <= 0:
        await ctx.send("❌ Le montant doit être positif.")
        return

    data = supabase.table("reiatsu").select("points").eq("user_id", str(member.id)).execute()

    if data.data:
        current = data.data[0]["points"]
        new_total = max(0, current - amount)
        supabase.table("reiatsu").update({"points": new_total}).eq("user_id", str(member.id)).execute()
        await ctx.send(f"✅ Retiré **-{amount}** points à {member.mention}. Nouveau total : **{new_total}**.")
    else:
        await ctx.send("❌ Ce membre n’a pas encore de Reiatsu enregistré.")
delreiatsu.category = "Reiatsu"



# spawn
# ─────────────────────────────────────────────

@bot.command(name="spawnreiatsu", aliases=["spawnrts"])
@commands.has_permissions(administrator=True)
async def spawnreiatsu(ctx):
    """Force le spawn d'un Reiatsu dans le salon configuré."""
    guild_id = ctx.guild.id
    channel = await get_reiatsu_channel(bot, guild_id)

    if channel is None:
        await ctx.send("❌ Aucun salon Reiatsu n'a été configuré. Utilisez `!setreiatsu` d'abord.")
        return

    embed = discord.Embed(
        title="💠 Un Reiatsu sauvage apparaît !",
        description="Cliquez sur la réaction 💠 pour l'absorber.",
        color=discord.Color.purple()
    )
    message = await channel.send(embed=embed)
    await message.add_reaction("💠")

    def check(reaction, user):  # ✅ Corrigé ici : aligné correctement
        return (
            reaction.message.id == message.id and 
            str(reaction.emoji) == "💠" and 
            not user.bot
        )

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=10800.0, check=check)  # 3h

        data = supabase.table("reiatsu").select("id", "points").eq("user_id", str(user.id)).execute()
        if data.data:
            current_points = data.data[0]["points"]
            supabase.table("reiatsu").update({"points": current_points + 1}).eq("user_id", str(user.id)).execute()
        else:
            supabase.table("reiatsu").insert({
                "user_id": str(user.id),
                "username": str(user.name),
                "points": 1
            }).execute()

        await channel.send(f"{user.mention} a absorbé le Reiatsu et gagné **+1** point !")
    except asyncio.TimeoutError:
        await channel.send("Le Reiatsu s'est dissipé dans l'air... personne ne l'a absorbé.")


spawnreiatsu.category = "Reiatsu"



# reiatsu channel
# ─────────────────────────────────────────────

@bot.command(name="reiatsuchannel", aliases=["rtschannel"])
@commands.has_permissions(administrator=True)
async def reiatsuchannel(ctx):
    """Affiche le salon configuré pour le spawn de Reiatsu."""
    guild_id = str(ctx.guild.id)

    data = supabase.table("reiatsu_config").select("channel_id").eq("guild_id", guild_id).execute()
    if data.data:
        channel_id = int(data.data[0]["channel_id"])
        channel = bot.get_channel(channel_id)
        if channel:
            await ctx.send(f"💠 Le salon configuré pour le spawn de Reiatsu est : {channel.mention}")
        else:
            await ctx.send("⚠️ Le salon configuré n'existe plus ou n'est pas accessible.")
    else:
        await ctx.send("❌ Aucun salon Reiatsu n’a encore été configuré avec `!setreiatsu`.")
reiatsuchannel.category = "Reiatsu"


# leaderbord général
# ─────────────────────────────────────────────

@bot.command(name="leaderboard", aliases=["toprts", "topreiatsu"])
async def leaderboard(ctx, limit: int = 10):
    """Affiche le classement des membres avec le plus de points de Reiatsu."""
    if limit < 1 or limit > 50:
        await ctx.send("❌ Le nombre d’entrées doit être entre 1 et 50.")
        return

    # Récupère les top utilisateurs
    result = supabase.table("reiatsu").select("username", "points").order("points", desc=True).limit(limit).execute()

    if not result.data:
        await ctx.send("📉 Aucun Reiatsu n’a encore été collecté.")
        return

    embed = discord.Embed(
        title=f"🏆 Classement Reiatsu - Top {limit}",
        description="Voici les utilisateurs avec le plus de points de Reiatsu.",
        color=discord.Color.purple()
    )

    for i, row in enumerate(result.data, start=1):
        username = row["username"]
        points = row["points"]
        embed.add_field(name=f"{i}. {username}", value=f"💠 {points} points", inline=False)

    await ctx.send(embed=embed)
leaderboard.category = "Reiatsu"

# pausereiatsu
# ─────────────────────────────────────────────

@bot.command(cname="pausereiatsu")
@commands.has_permissions(administrator=True)
async def pausereiatsu(ctx):
    if hasattr(bot, "reiatsu_spawner"):
        bot.reiatsu_spawner.pause()
        await ctx.send("⏸️ Le spawn automatique de Reiatsu est maintenant en pause.")
    else:
        await ctx.send("❌ Le spawner Reiatsu n'est pas actif.")
pausereiatsu.category = "Reiatsu"

# unpausereiatsu
# ─────────────────────────────────────────────

@bot.command(aliases=["resumerts"], name="unpausereiatsu")
@commands.has_permissions(administrator=True)
async def unpausereiatsu(ctx):
    if hasattr(bot, "reiatsu_spawner"):
        bot.reiatsu_spawner.resume()
        await ctx.send("▶️ Le spawn automatique de Reiatsu a repris.")
    else:
        await ctx.send("❌ Le spawner Reiatsu n'est pas actif.")
unpausereiatsu.category = "Reiatsu"

# temps reiatsu
# ─────────────────────────────────────────────

@bot.command(aliases=["tpsrts"], name="tempsreiatsu")
async def tempsreiatsu(ctx):
    guild_id = str(ctx.guild.id)
    config = supabase.table("reiatsu_config") \
        .select("last_spawn_at", "delay_minutes") \
        .eq("guild_id", guild_id).execute()

    if not config.data:
        await ctx.send("❌ Ce serveur n'a pas de config Reiatsu (`!setreiatsu`).")
        return

    conf = config.data[0]
    last_spawn_str = conf.get("last_spawn_at")
    last = parser.parse(last_spawn_str).timestamp() if last_spawn_str else 0
    delay = conf.get("delay_minutes") or 1800

    restant = max(0, (int(last) + int(delay)) - int(time.time()))
    if restant == 0:
        await ctx.send("💠 Le Reiatsu peut apparaître à tout moment !")
    else:
        minutes = restant // 60
        secondes = restant % 60
        await ctx.send(f"⏳ Prochain spawn automatique dans **{minutes}m {secondes}s**.")

tempsreiatsu.category = "Reiatsu"



# ─────────────────────────────────────────────
# général
# ─────────────────────────────────────────────



# Code 
# ─────────────────────────────────────────────

@bot.command(help="Affiche le lien du code du bot sur github.")
async def code(ctx):
    await ctx.send("🔗 Code source du bot : https://github.com/kevinraphael95/bleach-discord-bot-test")
code.category = "Général"


# 👋 Hello ##
# ─────────────────────────────────────────────

@bot.command(help="Affiche un message de bienvenue aléatoire.")
@commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
async def hello(ctx):
    try:
        with open("hello_messages.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            messages = data.get("messages", [])
        if messages:
            await ctx.send(random.choice(messages))
        else:
            await ctx.send("👋 Hello, je suis en ligne (mais sans message personnalisé) !")
    except FileNotFoundError:
        await ctx.send("❌ Fichier `hello_messages.json` introuvable.")
    except json.JSONDecodeError:
        await ctx.send("❌ Erreur de lecture du fichier `hello_messages.json`.")
hello.category = "Général"


# 📘 Commande : help 
# ─────────────────────────────────────────────

@bot.command(name="help", help="Affiche la liste des commandes ou les infos sur une commande spécifique.")
async def help_command(ctx, commande: str = None):
    prefix = get_prefix(bot, ctx.message)

    if commande is None:
        categories = {
            "Général": [],
            "Fun": [],
            "Reiatsu": [],
            "Admin": [],
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
        for cat in ["Général", "Fun", "Reiatsu", "Admin", "Autres"]:
            
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


# invitation 
# ─────────────────────────────────────────────

@bot.command(help="Affiche le lien d'invitation du bot.")
async def invitation(ctx):
    await ctx.send(f"🔗 Lien d'invitation du bot : {INVITE_URL}")
invitation.category = "Général"


# 🏓 Ping avec Embed + alias "test" ##
# ─────────────────────────────────────────────

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


# react
# ─────────────────────────────────────────────

@bot.command(aliases=["r"], name="react", help="Réagit au message ciblé avec un emoji animé, puis le retire après 3 minutes.")
async def react(ctx, emoji_name: str):
    try:
        await ctx.message.delete()
    except (discord.Forbidden, discord.HTTPException):
        pass

    name = emoji_name.strip(":").lower()

    emoji = next((e for e in ctx.guild.emojis if e.animated and e.name.lower() == name), None)
    if not emoji:
        await ctx.send(f"Emoji animé `:{name}:` introuvable sur ce serveur.", delete_after=5)
        return

    target_message = None

    if ctx.message.reference:
        try:
            target_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        except discord.NotFound:
            await ctx.send("Message référencé introuvable.", delete_after=5)
            return
    else:
        async for msg in ctx.channel.history(limit=20, before=ctx.message.created_at):
            if msg.id != ctx.message.id:
                target_message = msg
                break

    if not target_message or target_message.id == ctx.message.id:
        await ctx.send("Aucun message valide à réagir.", delete_after=5)
        return

    try:
        await target_message.add_reaction(emoji)
        print(f"Réaction {emoji} ajoutée au message {target_message.id}")
        await asyncio.sleep(180)
        await target_message.remove_reaction(emoji, ctx.guild.me)
        print(f"Réaction {emoji} retirée du message {target_message.id}")
    except Exception as e:
        print(f"Erreur en ajoutant/enlevant la réaction : {e}")
react.category = "Général"


# 🗣️ Say 
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# fun 
# ─────────────────────────────────────────────



# bleachmoji 
# ─────────────────────────────────────────────

@bot.command()
async def bmoji(ctx):
    try:
        with open("bleach_emojis.json", "r", encoding="utf-8") as f:
            personnages = json.load(f)

        if not personnages:
            await ctx.send("Le fichier d'emojis est vide.")
            return

        personnage = random.choice(personnages)
        nom = personnage.get("nom")
        emojis = personnage.get("emojis")

        if not nom or not emojis:
            await ctx.send("Erreur de format dans le fichier JSON.")
            return

        emoji_selection = random.choice(emojis)
        await ctx.send(f"{emoji_selection} → ||{nom}||")

    except FileNotFoundError:
        await ctx.send("❌ Fichier `bleach_emojis.json` introuvable.")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

bmoji.category = "Fun"


# cat 
# ─────────────────────────────────────────────

@bot.command(help="Montre une photo de chat")
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


# chiffre 
# ─────────────────────────────────────────────

# Suivi des jeux actifs par salon
active_games = {}

@bot.command(name="chiffre")
async def chiffre(ctx):
    if ctx.channel.id in active_games:
        await ctx.send("⚠️ Un jeu est déjà en cours dans ce salon. Attendez qu’il soit terminé ou utilisez `!cancel` pour l'annuler.")
        return

    number = random.randint(1, 100)
    await ctx.send(
        f"🎯 J'ai choisi un nombre entre 1 et 100. Le premier à répondre avec le bon nombre **dans ce salon** gagne ! Vous avez 1 heure.\n"
        f"🔍 (Réponse pour test : **{number}**)"
    )

    # Crée une tâche pour ce salon
    async def wait_for_answer():
        def check(m):
            return (
                m.channel == ctx.channel and
                m.author != bot.user and
                m.content.isdigit() and
                int(m.content) == number
            )
        try:
            msg = await bot.wait_for("message", timeout=3600.0, check=check)
            await ctx.send(f"🎉 Bravo {msg.author.mention}, tu as trouvé le nombre **{number}** !")
        except asyncio.TimeoutError:
            await ctx.send(f"⏰ Temps écoulé ! Personne n'a trouvé le nombre. C'était **{number}**.")
        finally:
            active_games.pop(ctx.channel.id, None)

    task = asyncio.create_task(wait_for_answer())
    active_games[ctx.channel.id] = task

@bot.command(name="cancel")
async def cancel(ctx):
    task = active_games.pop(ctx.channel.id, None)
    if task:
        task.cancel()
        await ctx.send("🚫 Le jeu a été annulé dans ce salon.")
    else:
        await ctx.send("❌ Aucun jeu en cours à annuler dans ce salon.")

# Optionnel : catégorisation
chiffre.category = "Fun"
cancel.category = "Fun"


# combat 
# ─────────────────────────────────────────────

@bot.command(name="combat", help="Simule un combat entre 2 personnages de Bleach avec stats et effets.")
async def combat(ctx):
    import random
    import json

    def format_etat_ligne(p):
        coeur = f"❤️ {max(p['vie'], 0)} PV"
        batterie = f"🔋 {p['energie']} énergie"
        if p["status"] == "gel":
            statut = f"❄️ Gelé ({p['status_duree']} tour)"
        elif p["status"] == "confusion":
            statut = f"💫 Confus ({p['status_duree']} tours)"
        elif p["status"] == "poison":
            statut = f"☠️ Empoisonné ({p['status_duree']} tours)"
        else:
            statut = "✅ Aucun effet"
        return f"{p['nom']} — {coeur} | {batterie} | {statut}"

    try:
        with open("bleach_personnages.json", "r", encoding="utf-8") as f:
            personnages = json.load(f)

        if len(personnages) < 2:
            await ctx.send("❌ Pas assez de personnages dans le fichier.")
            return

        p1, p2 = random.sample(personnages, 2)
        for p in (p1, p2):
            p["energie"] = 100
            p["vie"] = 100
            p["status"] = None
            p["status_duree"] = 0
            for atk in p["attaques"]:
                atk["utilisé"] = False

        p1_init = p1["stats"]["mobilité"] + random.randint(0, 10)
        p2_init = p2["stats"]["mobilité"] + random.randint(0, 10)
        tour_order = [p1, p2] if p1_init >= p2_init else [p2, p1]

        log = f"⚔️ **Combat entre {p1['nom']} et {p2['nom']} !**\n\n"

        for tour in range(1, 6):
            log += f"__🔁 Tour {tour}__\n\n"
            log += f"{format_etat_ligne(p1)}\n{format_etat_ligne(p2)}\n\n"

            for attaquant in tour_order:
                defenseur = p1 if attaquant == p2 else p2

                if attaquant["vie"] <= 0 or defenseur["vie"] <= 0:
                    continue

                if attaquant["status"] == "gel":
                    log += f"❄️ {attaquant['nom']} est gelé et ne peut pas agir.\n\n"
                    attaquant["status_duree"] -= 1
                    if attaquant["status_duree"] <= 0:
                        attaquant["status"] = None
                    continue

                if attaquant["status"] == "confusion":
                    if random.random() < 0.4:
                        log += f"💫 {attaquant['nom']} est confus et se blesse ! Il perd 10 PV.\n\n"
                        attaquant["vie"] -= 10
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None
                        continue

                if attaquant["status"] == "poison":
                    log += f"☠️ {attaquant['nom']} est empoisonné et perd 5 PV.\n"
                    attaquant["vie"] -= 5
                    attaquant["status_duree"] -= 1
                    if attaquant["status_duree"] <= 0:
                        attaquant["status"] = None

                possibles = [
                    a for a in attaquant["attaques"]
                    if a["cout"] <= attaquant["energie"] and (a["type"] != "ultime" or not a["utilisé"])
                ]
                if not possibles:
                    log += f"💤 {attaquant['nom']} n'a pas assez d'énergie pour attaquer.\n\n"
                    continue

                attaque = random.choice(possibles)
                if attaque["type"] == "ultime":
                    attaque["utilisé"] = True

                # Esquive
                esquive_chance = min(defenseur["stats"]["mobilité"] / 40 + random.uniform(0, 0.2), 0.5)
                tentative_esquive = random.random()
                cout_esquive = 50 if attaque["type"] == "ultime" else 10

                if tentative_esquive < esquive_chance:
                    if defenseur["energie"] >= cout_esquive:
                        defenseur["energie"] -= cout_esquive
                        log += f"💨 {defenseur['nom']} esquive l'attaque **{attaque['nom']}** avec le Shunpo ! (-{cout_esquive} énergie)\n"
                        if random.random() < 0.2:
                            contre = 10 + defenseur["stats"]["attaque"] // 2
                            attaquant["vie"] -= contre
                            log += f"🔁 {defenseur['nom']} contre-attaque et inflige {contre} dégâts à {attaquant['nom']} !\n"
                            if attaquant["vie"] <= 0:
                                log += f"\n🏆 **{defenseur['nom']} remporte le combat par contre-attaque !**"
                                await ctx.send(log)
                                return
                        log += "\n"
                        continue
                    else:
                        log += f"⚡ {defenseur['nom']} **aurait pu esquiver**, mais manque d'énergie !\n"

                base_degats = attaque["degats"]
                modificateur = (
                    attaquant["stats"]["attaque"]
                    + attaquant["stats"]["force"]
                    - defenseur["stats"]["défense"]
                    + attaquant["stats"]["pression"] // 5
                )
                total_degats = base_degats + max(0, modificateur)

                if random.random() < min(0.1 + attaquant["stats"]["force"] / 50, 0.4):
                    total_degats = int(total_degats * 1.5)
                    log += "💥 Coup critique ! Dégâts amplifiés !\n"

                defenseur["vie"] -= total_degats
                attaquant["energie"] -= attaque["cout"]

                log += (
                    f"💥 {attaquant['nom']} utilise **{attaque['nom']}** "
                    f"(coût : {attaque['cout']} énergie, dégâts : {base_degats}+bonus)\n"
                    f"➡️ {defenseur['nom']} perd {total_degats} PV\n"
                )

                effet = attaque["effet"].lower()
                if effet in ["gel", "paralysie"]:
                    defenseur["status"] = "gel"
                    defenseur["status_duree"] = 1
                    log += f"❄️ {defenseur['nom']} est gelé !\n"
                elif effet in ["confusion", "illusion"]:
                    defenseur["status"] = "confusion"
                    defenseur["status_duree"] = 2
                    log += f"💫 {defenseur['nom']} est confus pendant 2 tours !\n"
                elif effet in ["poison", "corrosion"]:
                    defenseur["status"] = "poison"
                    defenseur["status_duree"] = 3
                    log += f"☠️ {defenseur['nom']} est empoisonné !\n"

                if defenseur["vie"] <= 0:
                    log += f"\n🏆 **{attaquant['nom']} remporte le combat par KO !**"
                    await ctx.send(log)
                    return

                log += "\n"

        gagnant = p1 if p1["vie"] > p2["vie"] else p2
        log += f"__🧾 Résumé final__\n{format_etat_ligne(p1)}\n{format_etat_ligne(p2)}\n\n"
        log += f"🏁 **Fin du combat.**\n🏆 **{gagnant['nom']} l'emporte par avantage de vie !**"
        await ctx.send(log)

    except FileNotFoundError:
        await ctx.send("❌ Fichier `bleach_personnages.json` introuvable.")
    except Exception as e:
        await ctx.send(f"⚠️ Une erreur est survenue : {e}")
        

combat.category = "Fun"


# couleur 
# ─────────────────────────────────────────────

@bot.command(help="Montre une couleur aléatoire.")
async def couleur(ctx):
    # Génère une couleur aléatoire
    code_hex = random.randint(0, 0xFFFFFF)
    r = (code_hex >> 16) & 0xFF
    g = (code_hex >> 8) & 0xFF
    b = code_hex & 0xFF

    hex_str = f"#{code_hex:06X}"
    rgb_str = f"({r}, {g}, {b})"

    # Génère une image de prévisualisation via dummyimage
    image_url = f"https://dummyimage.com/300x100/{code_hex:06x}/{code_hex:06x}.png&text=%20"

    embed = discord.Embed(
        title="🎨 Couleur aléatoire",
        description=f"**Hex :** `{hex_str}`\n**RGB :** `{rgb_str}`",
        color=code_hex
    )
    embed.set_image(url=image_url)
    await ctx.send(embed=embed)
couleur.category = "Fun"


# dog 
# ─────────────────────────────────────────────

@bot.command(help="Montre une photo aléatoire d'un chien")
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


# emoji
# ─────────────────────────────────────────────

@bot.command(aliases=["e"], name="emoji")
async def emoji(ctx, *emoji_names):
    try:
        await ctx.message.delete()  # Supprime le message de commande
    except discord.Forbidden:
        pass  # Le bot n'a pas les permissions pour supprimer, ignore
    except discord.HTTPException:
        pass  # Une erreur s'est produite lors de la suppression, ignore

    if emoji_names:
        found = []
        not_found = []

        for raw_name in emoji_names:
            name = raw_name.strip(":").lower()
            match = next((e for e in ctx.guild.emojis if e.name.lower() == name), None)
            if match:
                found.append(str(match))
            else:
                not_found.append(raw_name)

        if found:
            await ctx.send(" ".join(found))

        if not_found:
            await ctx.send("❌ Emoji(s) introuvable(s) : " + ", ".join(f"`{name}`" for name in not_found))
    else:
        animated_emojis = [str(e) for e in ctx.guild.emojis if e.animated]
        if not animated_emojis:
            await ctx.send("❌ Ce serveur n'a aucun emoji animé.")
            return

        description = ""
        for emoji in animated_emojis:
            if len(description) + len(emoji) + 1 > 4096:
                await ctx.send(embed=discord.Embed(
                    title="🎞️ Emojis animés du serveur",
                    description=description,
                    color=discord.Color.purple()
                ))
                description = ""
            description += emoji + " "

        if description:
            await ctx.send(embed=discord.Embed(
                title="🎞️ Emojis animés du serveur",
                description=description,
                color=discord.Color.purple()
            ))
emoji.category = "Fun"




# funfact 
# ─────────────────────────────────────────────

@bot.command(help="Donne un funfact sur bleach écrit par chatgpt")
async def funfact(ctx):
    try:
        with open("funfacts_bleach.json", "r", encoding="utf-8") as f:
            facts = json.load(f)
        
        if not facts:
            await ctx.send("❌ Aucun fun fact disponible.")
            return
        
        fact = random.choice(facts)
        await ctx.send(f"🧠 **Fun Fact Bleach :** {fact}")
    except FileNotFoundError:
        await ctx.send("❌ Fichier `funfacts_bleach.json` introuvable.")
    except Exception as e:
        await ctx.send(f"⚠️ Une erreur est survenue : {e}")
funfact.category = "Fun"


# hollow
# ─────────────────────────────────────────────


@bot.command(name="hollow", help="Fait apparaître un Hollow à éliminer.")
@commands.cooldown(rate=1, per=60, type=commands.BucketType.channel)
async def hollow(ctx):
    embed = discord.Embed(
        title="⚠️ Un Hollow est apparu !",
        description="Réagis avec **☠️** pour le vaincre !",
        color=discord.Color.red()
    )
    embed.set_image(url="https://static.wikia.nocookie.net/bleach/images/e/e2/Ep1FishboneDProfile.png/revision/latest/thumbnail/width/360/height/360?cb=20210310035252&path-prefix=en")
    embed.set_footer(text="Sois rapide, ou il s'échappera...")

    message = await ctx.send(embed=embed)
    await message.add_reaction("☠️")

    def check(reaction, user):
        return (
            reaction.message.id == message.id and
            str(reaction.emoji) == "☠️" and
            not user.bot
        )

    try:
        reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check)
        await ctx.send(f"{user.mention} a vaincu le Hollow !")
    except asyncio.TimeoutError:
        await ctx.send("Le Hollow s'est échappé...")


# hollowify 
# ─────────────────────────────────────────────


@bot.command(help="Transforme un utilisateur en Hollow avec une description stylée.")
async def hollowify(ctx, member: discord.Member = None):
    member = member or ctx.author

    try:
        with open("hollow_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        prefixes = data.get("prefixes", [])
        suffixes = data.get("suffixes", [])
        descriptions = data.get("descriptions", [])

        if not prefixes or not suffixes or not descriptions:
            await ctx.send("❌ Le fichier hollow_data.json est incomplet ou mal formaté.")
            return

        nom_hollow = random.choice(prefixes) + random.choice(suffixes)
        description = random.choice(descriptions)

        await ctx.send(f"💀 **{member.display_name}** se transforme en Hollow : **{nom_hollow}** !\n{description}")

    except FileNotFoundError:
        await ctx.send("❌ Le fichier `hollow_data.json` est introuvable.")
    except Exception as e:
        await ctx.send(f"❌ Une erreur est survenue : {e}")

hollowify.category = "Fun"


# parti 
# ─────────────────────────────────────────────

@bot.command(help="Génère un nom de parti politique aléatoire.")
async def parti(ctx):
    with open("partis_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    premiers_mots = data["premiers_mots"]
    adjectifs = data["adjectifs"]
    noms = data["noms"]

    nom_parti = f"{random.choice(premiers_mots)} {random.choice(adjectifs)} {random.choice(noms)}"
    await ctx.send(f"🏛️ Voici un nom de parti politique : **{nom_parti}**")
parti.category = "Fun"


# perso 
# ─────────────────────────────────────────────

@bot.command(help="Découvre quel personnage de Bleach tu es (toujours le même pour toi).")
async def perso(ctx):
    try:
        with open("bleach_characters.json", "r", encoding="utf-8") as f:
            characters = json.load(f)

        if not characters or not isinstance(characters, list):
            await ctx.send("❌ Le fichier des personnages est vide ou invalide.")
            return

        user_id = ctx.author.id
        index = (user_id * 31 + 17) % len(characters)
        personnage = characters[index]
        await ctx.send(f"{ctx.author.mention}, tu es **{personnage}** ! (C'est ta destinée dans le monde de Bleach 🔥)")

    except FileNotFoundError:
        await ctx.send("❌ Fichier `bleach_characters.json` introuvable.")
    except json.JSONDecodeError:
        await ctx.send("❌ Le fichier JSON est mal formaté.")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

perso.category = "Fun"



# phrase 
# ─────────────────────────────────────────────

@bot.command(name="phrase", help="Génère une phrase aléatoire avec accords (via JSON).")
async def phrase(ctx):
    try:
        with open("phrases_listes.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        sujet_data = random.choice(data["sujets"])
        sujet = sujet_data["mot"]
        genre_sujet = sujet_data["genre"]

        verbe = random.choice(data["verbes"])

        complement_data = random.choice(data["complements"])
        complement = complement_data["mot"]
        genre_complement = complement_data["genre"]

        adverbe = random.choice(data["adverbes"])

        # Article pour le sujet
        if sujet[0].lower() in "aeiou":
            article_sujet = "L'"
        else:
            article_sujet = "Le " if genre_sujet == "m" else "La "

        # Article pour le complément
        if complement[0].lower() in "aeiou":
            article_complement = "l'"
        else:
            article_complement = "le " if genre_complement == "m" else "la "

        phrase_complete = f"{article_sujet}{sujet} {verbe} {article_complement}{complement} {adverbe}."

        await ctx.send(phrase_complete)

    except FileNotFoundError:
        await ctx.send("❌ Fichier `phrases_listes.json` introuvable.")
    except Exception as e:
        await ctx.send(f"⚠️ Une erreur est survenue : {e}")

phrase.category = "Fun"


# 🪙 Pile ou face 
# ─────────────────────────────────────────────

@bot.command(help="Lance une pièce : pile ou face.")
async def pof(ctx):
    resultat = random.choice(["🪙 Pile !", "🪙 Face !"])
    await ctx.send(resultat)
pof.category = "Fun"


# pps 
# ─────────────────────────────────────────────

@bot.command()
async def pps(ctx, adversaire: discord.Member = None):
    joueur1 = ctx.author
    joueur2 = adversaire or bot.user  # Si aucun adversaire : bot

    emojis = {
        "shinigami": "🗡️",
        "quincy": "🎯",
        "hollow": "💀"
    }

    forces = {
        "shinigami": "hollow",
        "hollow": "quincy",
        "quincy": "shinigami"
    }

    message = await ctx.send(f"**{joueur1.mention}**, choisis ta race :\n🗡️ Shinigami — 🎯 Quincy — 💀 Hollow")

    for emoji in emojis.values():
        await message.add_reaction(emoji)

    def check_reaction(reaction, user):
        return user == joueur1 and str(reaction.emoji) in emojis.values() and reaction.message.id == message.id

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
    except asyncio.TimeoutError:
        return await ctx.send("⏰ Temps écoulé. Partie annulée.")

    choix_j1 = next(race for race, emoji in emojis.items() if emoji == str(reaction.emoji))

    if joueur2 == bot.user:
        choix_j2 = random.choice(list(emojis.keys()))
    else:
        await ctx.send(f"**{joueur2.mention}**, à toi de choisir :\n🗡️ Shinigami — 🎯 Quincy — 💀 Hollow")
        message2 = await ctx.send("Réagis avec ton choix.")
        for emoji in emojis.values():
            await message2.add_reaction(emoji)

        def check_reaction_2(reaction, user):
            return user == joueur2 and str(reaction.emoji) in emojis.values() and reaction.message.id == message2.id

        try:
            reaction2, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check_reaction_2)
        except asyncio.TimeoutError:
            return await ctx.send("⏰ Temps écoulé pour le second joueur. Partie annulée.")

        choix_j2 = next(race for race, emoji in emojis.items() if emoji == str(reaction2.emoji))

    # Résultat
    gagnant = None
    if choix_j1 == choix_j2:
        result = "⚖️ Égalité parfaite entre deux âmes puissantes !"
    elif forces[choix_j1] == choix_j2:
        gagnant = joueur1
        result = f"🏆 **{joueur1.display_name}** l’emporte ! {emojis[choix_j1]} bat {emojis[choix_j2]}"
    else:
        gagnant = joueur2
        result = f"🏆 **{joueur2.display_name}** l’emporte ! {emojis[choix_j2]} bat {emojis[choix_j1]}"

    await ctx.send(
        f"{joueur1.display_name} : {emojis[choix_j1]} {choix_j1.capitalize()}  \n"
        f"{joueur2.display_name} : {emojis[choix_j2]} {choix_j2.capitalize()}\n\n"
        f"{result}"
    )

pps.category = "Fun"


# recommande 
# ─────────────────────────────────────────────

@bot.command(help="commande + solo ou multi. Le bot te recommande un jeu avec année et genre.")
async def recommande(ctx, type_jeu: str = None):
    import json
    import random

    if type_jeu is None:
        await ctx.send("❗ Utilise la commande avec `solo` ou `multi` pour obtenir une recommandation.")
        return

    type_jeu = type_jeu.lower()

    try:
        with open("jeux.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        await ctx.send("❌ Le fichier `jeux.json` est introuvable.")
        return
    except json.JSONDecodeError:
        await ctx.send("❌ Le fichier `jeux.json` est mal formé.")
        return

    if type_jeu not in data:
        await ctx.send("❗ Spécifie soit `solo` soit `multi`.")
        return

    jeux = data[type_jeu]
    if not jeux:
        await ctx.send(f"⚠️ Aucun jeu {type_jeu} trouvé.")
        return

    jeu = random.choice(jeux)
    titre = jeu.get("titre", "Jeu inconnu")
    annee = jeu.get("annee", "année inconnue")
    genre = jeu.get("genre", "genre inconnu")

    await ctx.send(
        f"🎮 Jeu **{type_jeu}** recommandé : **{titre}**\n"
        f"🗓️ Année : {annee} | 🧩 Genre : {genre}"
    )

recommande.category = "Fun"


# ship 
# ─────────────────────────────────────────────

@bot.command()
async def ship(ctx):
    import json
    import hashlib
    import random

    try:
        with open("bleach_personnages.json", "r", encoding="utf-8") as f:
            persos = json.load(f)

        if len(persos) < 2:
            await ctx.send("❌ Il faut au moins deux personnages dans `bleach_personnages.json`.")
            return

        # Choisir deux personnages différents au hasard
        p1, p2 = random.sample(persos, 2)

        # Toujours le même résultat pour un même couple : on trie les noms
        noms_ordonnes = sorted([p1["nom"], p2["nom"]])
        clef = f"{noms_ordonnes[0]}+{noms_ordonnes[1]}"

        # Hash déterministe pour score de 0 à 100
        hash_bytes = hashlib.md5(clef.encode()).digest()
        score = int.from_bytes(hash_bytes, 'big') % 101

        # Réaction selon le score
        if score >= 90:
            reaction = "âmes sœurs ! 💞"
        elif score >= 70:
            reaction = "excellente alchimie ! 🔥"
        elif score >= 50:
            reaction = "bonne entente. 😊"
        elif score >= 30:
            reaction = "relation compliquée... 😬"
        else:
            reaction = "aucune chance ! 💔"

        await ctx.send(f"**{p1['nom']}** ❤️ **{p2['nom']}** → Compatibilité : **{score}%** — {reaction}")

    except FileNotFoundError:
        await ctx.send("❌ Fichier `bleach_personnages.json` introuvable.")
    except Exception as e:
        await ctx.send(f"⚠️ Erreur : {e}")

ship.category = "Fun"


# versus 
# ─────────────────────────────────────────────

@bot.command(name="versus", help="Combat interactif entre deux joueurs avec des personnages Bleach.")
async def versus(ctx):
    with open("bleach_personnages.json", "r", encoding="utf-8") as f:
        personnages = json.load(f)

    message_invite = await ctx.send("🧑‍🤝‍🧑 Deux joueurs doivent réagir avec ✋ pour rejoindre le combat.")
    await message_invite.add_reaction("✋")

    joueurs = []

    def check_reaction(reaction, user):
        return reaction.message.id == message_invite.id and str(reaction.emoji) == "✋" and user != bot.user and user not in joueurs

    while len(joueurs) < 2:
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=60.0, check=check_reaction)
            joueurs.append(user)
            await ctx.send(f"✅ {user.mention} a rejoint le combat.")
        except asyncio.TimeoutError:
            await ctx.send("⏰ Temps écoulé. Le combat est annulé.")
            return

    # Attribution aléatoire des personnages
    p1_data, p2_data = random.sample(personnages, 2)
    p1_data["joueur"], p2_data["joueur"] = joueurs[0], joueurs[1]

    for perso in (p1_data, p2_data):
        perso["vie"] = 100
        perso["energie"] = 100
        perso["status"] = None
        perso["status_duree"] = 0
        for atk in perso["attaques"]:
            atk["utilisé"] = False

    await ctx.send(f"🎮 **{joueurs[0].mention} ({p1_data['nom']}) VS {joueurs[1].mention} ({p2_data['nom']}) !**")

    def format_etat(p):
        status = "✅ Aucun effet"
        if p["status"] == "gel":
            status = f"❄️ Gelé ({p['status_duree']} tour)"
        elif p["status"] == "confusion":
            status = f"💫 Confus ({p['status_duree']} tours)"
        elif p["status"] == "poison":
            status = f"☠️ Empoisonné ({p['status_duree']} tours)"
        return f"{p['nom']} ({p['joueur'].mention}) — ❤️ {p['vie']} PV | 🔋 {p['energie']} énergie | {status}"

    async def jouer_tour(joueur_data, adverse_data):
        if joueur_data["status"] == "gel":
            joueur_data["status_duree"] -= 1
            if joueur_data["status_duree"] <= 0:
                joueur_data["status"] = None
            await ctx.send(f"❄️ {joueur_data['nom']} est gelé et ne peut pas agir.")
            return

        if joueur_data["status"] == "poison":
            joueur_data["vie"] -= 5
            joueur_data["status_duree"] -= 1
            if joueur_data["status_duree"] <= 0:
                joueur_data["status"] = None
            await ctx.send(f"☠️ {joueur_data['nom']} perd 5 PV à cause du poison.")

        if joueur_data["status"] == "confusion":
            if random.random() < 0.4:
                joueur_data["vie"] -= 10
                joueur_data["status_duree"] -= 1
                if joueur_data["status_duree"] <= 0:
                    joueur_data["status"] = None
                await ctx.send(f"💫 {joueur_data['nom']} est confus et se blesse ! (-10 PV)")
                return

        attaques_dispo = [a for a in joueur_data["attaques"] if a["cout"] <= joueur_data["energie"] and (a["type"] != "ultime" or not a["utilisé"])]
        if not attaques_dispo:
            await ctx.send(f"💤 {joueur_data['nom']} n’a pas assez d’énergie pour attaquer.")
            return

        options = [SelectOption(label=a["nom"], description=f"{a['type']} - {a['cout']} énergie") for a in attaques_dispo]

        class AttaqueSelect(Select):
            def __init__(self):
                super().__init__(placeholder="Choisissez une attaque", options=options)

            async def callback(self, interaction: Interaction):
                if interaction.user != joueur_data["joueur"]:
                    await interaction.response.send_message("Ce n’est pas ton tour !", ephemeral=True)
                    return

                attaque = next(a for a in attaques_dispo if a["nom"] == self.values[0])
                if attaque["type"] == "ultime":
                    attaque["utilisé"] = True

                esquive_chance = min(adverse_data["stats"]["mobilité"] / 40 + random.uniform(0, 0.2), 0.5)
                esquive = random.random() < esquive_chance and adverse_data["energie"] >= 10

                log = ""
                if esquive:
                    cout = 50 if attaque["type"] == "ultime" else 10
                    adverse_data["energie"] -= cout
                    log += f"💨 {adverse_data['nom']} esquive l'attaque ! (-{cout} énergie)"
                else:
                    base = attaque["degats"]
                    mod = joueur_data["stats"]["attaque"] + joueur_data["stats"]["force"] - adverse_data["stats"]["défense"]
                    total = base + max(0, mod)
                    if random.random() < min(0.1 + joueur_data["stats"]["force"] / 50, 0.4):
                        total = int(total * 1.5)
                        log += "💥 Coup critique !\n"
                    adverse_data["vie"] -= total
                    joueur_data["energie"] -= attaque["cout"]
                    log += f"{joueur_data['nom']} utilise **{attaque['nom']}** : {total} dégâts."

                    effet = attaque["effet"].lower()
                    if effet == "gel":
                        adverse_data["status"] = "gel"
                        adverse_data["status_duree"] = 1
                        log += f"\n❄️ {adverse_data['nom']} est gelé !"
                    elif effet == "confusion":
                        adverse_data["status"] = "confusion"
                        adverse_data["status_duree"] = 2
                        log += f"\n💫 {adverse_data['nom']} est confus !"
                    elif effet == "poison":
                        adverse_data["status"] = "poison"
                        adverse_data["status_duree"] = 3
                        log += f"\n☠️ {adverse_data['nom']} est empoisonné !"

                await interaction.response.edit_message(content=log + "\n\n" + format_etat(joueur_data) + "\n" + format_etat(adverse_data), view=None)
                interaction.client._next_turn.set_result(True)  # pour avancer dans la boucle

        view = View()
        view.add_item(AttaqueSelect())
        await ctx.send(f"🎯 {joueur_data['joueur'].mention}, c'est à vous de jouer :", view=view)

        bot._next_turn = asyncio.get_event_loop().create_future()
        try:
            await asyncio.wait_for(bot._next_turn, timeout=60)
        except asyncio.TimeoutError:
            await ctx.send("⏰ Temps écoulé pour choisir une attaque.")

    combat_terminé = False
    tour = 1
    while not combat_terminé and tour <= 5:
        await ctx.send(f"🔁 **Tour {tour}**")
        await ctx.send(format_etat(p1_data) + "\n" + format_etat(p2_data))

        for j, adv in [(p1_data, p2_data), (p2_data, p1_data)]:
            if j["vie"] <= 0:
                combat_terminé = True
                break
            await jouer_tour(j, adv)
            if adv["vie"] <= 0:
                await ctx.send(f"🏆 **{j['nom']} remporte le combat !**")
                combat_terminé = True
                break
        tour += 1

    if not combat_terminé:
        gagnant = p1_data if p1_data["vie"] > p2_data["vie"] else p2_data
        await ctx.send(f"🏁 Fin du combat après 5 tours. **{gagnant['nom']} gagne par PV restants !**")

versus.category = "Fun"





# ─────────────────────────────────────────────
# admin 
# ─────────────────────────────────────────────


# 🔧 Préfixe (admin uniquement) 
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# en cas d'erreur
# ─────────────────────────────────────────────

@bot.event
async def on_command_error(ctx, error):
    if not IS_MAIN_INSTANCE:
        return  # Ignore les erreurs sur les instances secondaires

    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"🕒 Patiente un peu ! Réessaie dans {error.retry_after:.1f} secondes.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Cette commande n'existe pas.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("⚠️ Il manque un argument à ta commande.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Tu n’as pas la permission pour cette commande.")
    else:
        await ctx.send("⚠️ Une erreur est survenue.")
        raise error




# Debug infos
print("Dossier de travail actuel :", os.getcwd())
print("Fichiers dans le dossier :", os.listdir())



# ─────────────────────────────────────────────
# ▶️ Lancement
# ─────────────────────────────────────────────


# Démarre le serveur web pour le keep-alive
keep_alive()
# Lancer le bot
bot.run(TOKEN)
