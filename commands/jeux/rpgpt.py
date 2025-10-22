# ────────────────────────────────────────────────────────────────────────────────
# 📌 rpgpt.py — Mini RPG Bleach (Les Fissures du Néant) amélioré
# Commande /rpgpt et !rpgpt avec persistance Supabase et gestion sécurisée Discord
# Objectif : Mini RPG narratif où le joueur répond avec un mot ou une phrase précédé de "!"
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from utils.gpt_oss_client import get_story_continuation
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
Le joueur incarne un shinigami (ou âme errante) explorant les fissures reliant le Seireitei et le Hueco Mundo.

L’histoire suit trois actes :
1️⃣ Découverte des fissures.
2️⃣ Rencontre d’un allié ambigu.
3️⃣ Choix final face au Néant.

Tu adaptes tes descriptions à ses choix (réponses précédées de "!"), tu ajoutes des indices et de la tension.
L’ambiance doit être immersive, poétique et mystérieuse. Ne révèle pas la fin trop tôt.
"""

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class RPGPT(commands.Cog):
    """Commande /rpgpt et !rpgpt — Mini RPG narratif (Bleach) avec persistance Supabase"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions = {}

    # ────────────────────────────────────────────────────────────────────────────
    # 🧱 Démarrage d’une session
    # ────────────────────────────────────────────────────────────────────────────
    async def start_session(self, user: discord.User, channel: discord.TextChannel):
        active_players = supabase.table("players").select("*").execute().data
        if len(active_players) >= MAX_ACTIVE_PLAYERS and not any(p["discord_id"] == user.id for p in active_players):
            await safe_send(channel, "🚫 Trop de shinigamis enquêtent déjà sur les fissures. Réessaie plus tard !")
            return

        result = supabase.table("players").select("*").eq("discord_id", user.id).execute()
        player = result.data[0] if result.data else None

        if player:
            # Reprise de partie
            history = player["history"]
            turns = player["turns"]
            await safe_send(channel, "🌫️ *Le vent du Néant souffle à nouveau...*")
        else:
            # Nouvelle partie — grande introduction
            intro = (
                "🌌 **Bienvenue, âme errante...**\n\n"
                "Tu es sur le point de plonger dans *Les Fissures du Néant*, un mini-RPG inspiré de Bleach.\n"
                "Le principe est simple : tu peux répondre par **un mot ou une phrase**, précédé de `!`.\n\n"
                "Exemples : `!attaque`, `!parle à l’allié`, `!observe le couloir`\n\n"
                "Ton choix influencera le cours de l’histoire.\n\n"
                "🌒 **Acte I — Le Frisson du Vide**\n"
                "Un souffle froid parcourt le Seireitei. Une fissure s’ouvre entre deux mondes...\n\n"
                "Que fais-tu ? (`!attaque`, `!observe`, `!fuis`)"
            )

            history = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": intro}
            ]
            turns = 0

            supabase.table("players").insert({
                "discord_id": user.id,
                "history": history,
                "turns": turns,
                "last_channel": str(channel.id)
            }).execute()

        self.sessions[user.id] = {"history": history, "turns": turns, "channel": channel}
        await safe_send(channel, history[-1]["content"])

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="rpgpt", description="Lance une mini-aventure RPG inspirée de Bleach. RPG + chat gpt.")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_rpgpt(self, interaction: discord.Interaction):
        await safe_respond(interaction, "✨ L’aventure commence...", ephemeral=True)
        await self.start_session(interaction.user, interaction.channel)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="rpgpt", help="Lance une mini-aventure RPG inspirée de Bleach. RPG + chat gpt.")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_rpgpt(self, ctx: commands.Context):
        await self.start_session(ctx.author, ctx.channel)

    # ────────────────────────────────────────────────────────────────────────────
    # 🧩 Listener : réponses du joueur (commencent par "!")
    # ────────────────────────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        user_id = message.author.id
        if user_id not in self.sessions:
            return

        session = self.sessions[user_id]
        if message.channel != session["channel"]:
            return

        content = message.content.strip()

        # Vérifie que le message commence par "!"
        if not content.startswith("!"):
            return

        # On accepte tout après "!" sans limite de mots
        mot = content[1:].strip()
        if not mot:
            await safe_send(message.channel, "❌ Écris quelque chose après `!`.")
            return

        # Ajout du tour dans l’historique
        session["history"].append({"role": "user", "content": mot})
        session["turns"] += 1

        try:
            response = await asyncio.to_thread(get_story_continuation, session["history"])
        except Exception as e:
            await safe_send(message.channel, "⚠️ Le narrateur se tait... (*limite atteinte ou erreur API*)")
            print(f"[Erreur RPGPT] {e}")
            del self.sessions[user_id]
            return

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
            command.category = "Jeux"
    await bot.add_cog(cog)
