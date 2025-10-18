# ────────────────────────────────────────────────────────────────────────────────
# 📌 rpgpt.py — Mini RPG Bleach (Les Fissures du Néant) amélioré
# Commande /rpgpt et !rpgpt avec persistance Supabase et gestion sécurisée Discord
# Objectif : Mini RPG narratif où le joueur répond avec un seul mot.
# Catégorie : Jeu / RPG
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.openai_client import get_story_continuation
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Configuration
# ────────────────────────────────────────────────────────────────────────────────
MAX_ACTIVE_PLAYERS = 3
MAX_TURNS = 10

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Prompt système — trame de base
# ────────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
Tu es le narrateur d’un mini-RPG textuel inspiré de *Bleach*, intitulé **Les Fissures du Néant**.
Le joueur incarne un shinigami (ou âme errante) explorant les fissures qui relient le Seireitei et le Hueco Mundo.
L’histoire suit trois actes :
1️⃣ Découverte des fissures
2️⃣ Rencontre d’un allié ambigu
3️⃣ Choix final face au Néant

Tu adaptes tes descriptions à ses choix (réponses d’un seul mot), tu ajoutes des indices et de la tension.
L’ambiance doit être immersive, poétique et mystérieuse. Ne révèle pas la fin trop tôt.
"""

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class RPGPT(commands.Cog):
    """Commande /rpgpt et !rpgpt — Mini RPG narratif (Bleach) avec persistance Supabase"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions = {}  # session locale pour suivre le canal et limiter les tours en mémoire

    # ────────────────────────────────────────────────────────────────────────────
    # 🧱 Démarrage d’une session
    # ────────────────────────────────────────────────────────────────────────────
    async def start_session(self, user: discord.User, channel: discord.TextChannel):
        # Vérifie limite active
        active_players = supabase.table("players").select("*").execute().data
        if len(active_players) >= MAX_ACTIVE_PLAYERS and not any(p["discord_id"] == user.id for p in active_players):
            await safe_send(channel, "🚫 Trop de shinigamis enquêtent déjà sur les fissures. Réessaie plus tard !")
            return

        # Récupère ou crée le joueur
        result = supabase.table("players").select("*").eq("discord_id", user.id).execute()
        player = result.data[0] if result.data else None

        if player:
            history = player["history"]
            turns = player["turns"]
        else:
            history = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": "🌫️ Un vent glacial traverse le Seireitei... Choisis un mot : attaque, parle, fuis."}
            ]
            turns = 0
            supabase.table("players").insert({
                "discord_id": user.id,
                "history": history,
                "turns": turns,
                "last_channel": str(channel.id)
            }).execute()

        # Sauvegarde localement la session
        self.sessions[user.id] = {"history": history, "turns": turns, "channel": channel}

        await safe_send(channel, history[-1]["content"])

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="rpgpt",
        description="Lance une mini-aventure RPG inspirée de Bleach."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_rpgpt(self, interaction: discord.Interaction):
        await safe_respond(interaction, "✨ L’aventure commence...", ephemeral=True)
        await self.start_session(interaction.user, interaction.channel)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="rpgpt")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_rpgpt(self, ctx: commands.Context):
        await self.start_session(ctx.author, ctx.channel)

    # ────────────────────────────────────────────────────────────────────────────
    # 🧩 Listener : réponses du joueur
    # ────────────────────────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        user_id = message.author.id
        if user_id not in self.sessions:
            return

        session = self.sessions[user_id]

        # Ignore si message pas dans le même salon
        if message.channel != session["channel"]:
            return

        # Vérifie mot unique
        content = message.content.strip()
        if len(content.split()) > 1:
            await safe_send(message.channel, "❌ Un seul mot à la fois, shinigami.")
            return

        # Limite de tours
        if session["turns"] >= MAX_TURNS:
            await safe_send(message.channel, "🌙 *Ton aventure touche à sa fin...* Le Néant se referme.")
            del self.sessions[user_id]
            supabase.table("players").delete().eq("discord_id", user_id).execute()
            return

        # Ajoute la réponse à l’historique
        session["history"].append({"role": "user", "content": content})
        session["turns"] += 1

        # Appel OpenAI
        try:
            response = await asyncio.to_thread(get_story_continuation, session["history"])
        except Exception as e:
            await safe_send(message.channel, "⚠️ Le narrateur se tait... (*limite atteinte ou erreur API*)")
            print(f"[Erreur RPGPT] {e}")
            del self.sessions[user_id]
            return

        # Met à jour l’historique local et Supabase
        session["history"].append({"role": "assistant", "content": response})
        supabase.table("players").update({
            "history": session["history"],
            "turns": session["turns"],
            "last_channel": str(message.channel.id)
        }).eq("discord_id", user_id).execute()

        await safe_send(message.channel, response)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = RPGPT(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeu / RPG"
    await bot.add_cog(cog)
