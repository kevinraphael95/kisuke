# ────────────────────────────────────────────────────────────────────────────────
# 📌 rpgpt.py — Mini RPG Bleach (Les Fissures du Néant) v7 corrigé
# Commande /rpgpt et !rpgpt avec persistance Supabase et JDR complet
# Objectif : Mini RPG narratif où le joueur répond avec un seul mot précédé de "!"
# Tout mot est reconnu et reçoit toujours une réponse
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime
from utils.gpt_oss_client import get_story_continuation
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond
import random

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Configuration
# ────────────────────────────────────────────────────────────────────────────────
MAX_ACTIVE_PLAYERS = 3
SESSION_TIMEOUT = 600  # 10 minutes d’inactivité

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Prompt système
# ────────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
Tu es le narrateur d’un mini-RPG textuel inspiré de Bleach, intitulé Les Fissures du Néant.
Le joueur incarne un shinigami explorant les fissures Seireitei ↔ Hueco Mundo.
Adapte tes descriptions à ses choix, stats et inventaire.
Chaque action doit influencer le récit et l’univers.
"""

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class RPGPT(commands.Cog):
    """Commande /rpgpt et !rpgpt — RPG narratif avec stats, inventaire et JDR complet."""

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
            stats = player.get("stats", {"pv": 100, "force": 10, "agilite": 8, "reiatsu": 15, "chance": 5})
            inventory = player.get("inventory", [{"nom": "Zanpakuto", "effet": "attaque +5"}])
            save_state = player.get("save_state", {"acte": 1, "choix_importants": []})
            await safe_send(channel, "🌫️ *Le vent du Néant souffle à nouveau...*")
        else:
            # Nouvelle partie
            intro = (
                "🌌 **Bienvenue, âme errante...**\n\n"
                "Tu es sur le point de plonger dans *Les Fissures du Néant*.\n"
                "Réponds avec **un seul mot** précédé de `!`.\n\n"
                "Exemples : `!attaque`, `!observe`, `!parle`\n\n"
                "🌒 **Acte I — Le Frisson du Vide**\n"
                "Une fissure s’ouvre entre deux mondes... Que fais-tu ? (`!attaque`, `!observe`, `!fuis`)"
            )
            history = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "assistant", "content": intro}]
            stats = {"pv": 100, "force": 10, "agilite": 8, "reiatsu": 15, "chance": 5}
            inventory = [{"nom": "Zanpakuto", "effet": "attaque +5"}]
            save_state = {"acte": 1, "choix_importants": []}

            supabase.table("players").insert({
                "discord_id": user.id,
                "history": history,
                "stats": stats,
                "inventory": inventory,
                "save_state": save_state,
                "last_channel": str(channel.id)
            }).execute()
            await safe_send(channel, history[-1]["content"])

        self.sessions[user.id] = {
            "history": history,
            "stats": stats,
            "inventory": inventory,
            "save_state": save_state,
            "channel": channel,
            "last_activity": datetime.utcnow()
        }

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="rpgpt", description="Lance une mini-aventure RPG.")
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
        if message.author.bot: return
        user_id = message.author.id
        if user_id not in self.sessions: return

        session = self.sessions[user_id]
        if message.channel != session["channel"]: return

        content = message.content.strip()
        if not content.startswith("!"): return

        mot = content[1:].strip()
        if not mot or len(mot.split()) > 1:
            await safe_send(message.channel, "❌ Un seul mot précédé de `!` !")
            return

        # ⚡ Ajout à l’historique
        session["history"].append({"role": "user", "content": mot})
        session["last_activity"] = datetime.utcnow()

        # ⚔️ Gestion simple d’actions pour stats et inventaire
        if mot.lower() == "attaque":
            degats = random.randint(5, 15) + session["stats"]["force"]
            session["stats"]["pv"] = max(0, session["stats"]["pv"] - degats//2)
            session["save_state"]["choix_importants"].append("attaque")
        elif mot.lower() == "fuis":
            session["stats"]["agilite"] += 2
            session["save_state"]["choix_importants"].append("fuis")
        elif mot.lower() == "observe":
            session["stats"]["chance"] += 1
            session["save_state"]["choix_importants"].append("observe")
        elif mot.lower() == "utilise" and session["inventory"]:
            item = session["inventory"].pop(0)
            session["stats"]["pv"] = min(100, session["stats"]["pv"] + 20)
            session["save_state"]["choix_importants"].append(f"utilisé {item['nom']}")

        # ⚡ Appel GPT pour générer la suite
        try:
            context = session["history"] + [{"role": "system", "content": f"Stats: {session['stats']}, Inventory: {session['inventory']}"}]
            response = await asyncio.to_thread(get_story_continuation, context)
        except Exception as e:
            await safe_send(message.channel, "⚠️ Le narrateur se tait...")
            print(f"[Erreur RPGPT] {e}")
            return

        session["history"].append({"role": "assistant", "content": response})

        # ⚡ Mise à jour Supabase
        supabase.table("players").upsert({
            "discord_id": user_id,
            "history": session["history"],
            "stats": session["stats"],
            "inventory": session["inventory"],
            "save_state": session["save_state"],
            "last_channel": str(message.channel.id)
        }).execute()

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
