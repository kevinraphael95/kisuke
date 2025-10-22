# ────────────────────────────────────────────────────────────────────────────────
# 📌 rpgpt.py — Mini RPG Bleach (Les Fissures du Néant) v6 libre
# Commande /rpgpt et !rpgpt avec JDR complet : stats, inventaire interactif, save_state
# Objectif : RPG narratif immersif sans limite de tours, fin basée sur PV ou progression
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands, tasks
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
SESSION_TIMEOUT = 600  # 10 minutes

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Prompt système
# ────────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
Tu es le narrateur d’un mini-RPG narratif inspiré de Bleach.
Le joueur incarne un shinigami explorant les fissures Seireitei ↔ Hueco Mundo.
Adapte tes descriptions à ses choix, stats et inventaire. Intègre combats et événements dynamiques.
"""

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class RPGPT(commands.Cog):
    """RPG narratif complet avec JDR, stats dynamiques, inventaire interactif et combats."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions = {}
        self.cleanup_sessions.start()

    # ────────────────────────────────────────────────────────────────────────────
    # 🧽 Nettoyage automatique des sessions inactives
    # ────────────────────────────────────────────────────────────────────────────
    @tasks.loop(minutes=5)
    async def cleanup_sessions(self):
        now = datetime.utcnow()
        expired = [uid for uid, s in self.sessions.items()
                   if (now - s["last_activity"]).total_seconds() > SESSION_TIMEOUT]
        for uid in expired:
            del self.sessions[uid]

    # ────────────────────────────────────────────────────────────────────────────
    # 🧱 Création d’un embed d’introduction immersive
    # ────────────────────────────────────────────────────────────────────────────
    def build_intro_embed(self, user: discord.User) -> discord.Embed:
        embed = discord.Embed(
            title="🌌 Les Fissures du Néant",
            description="Un souffle glacial traverse le Seireitei. Une fissure s’ouvre vers Hueco Mundo...",
            color=discord.Color.dark_purple()
        )
        embed.add_field(
            name="🌀 Synopsis",
            value="Tu incarnes un shinigami pris dans les Fissures du Néant. Chaque choix influencera le récit, tes stats et ton inventaire.",
            inline=False
        )
        embed.add_field(
            name="⚔️ Règles du jeu",
            value="Réponds avec **un seul mot** précédé de `!`.\nExemples : `!attaque`, `!observe`, `!parle`, `!fuis`, `!utilise`",
            inline=False
        )
        embed.add_field(
            name="🌒 Acte I — Le Frisson du Vide",
            value="Une fissure se matérialise devant toi, aspirant la lumière. Que fais-tu ? (`!observe`, `!attaque`, `!fuis`)",
            inline=False
        )
        embed.set_footer(text=f"Mini-RPG narratif • Invocateur : {user.display_name}")
        return embed

    # ────────────────────────────────────────────────────────────────────────────
    # 🧱 Embed de stats et inventaire
    # ────────────────────────────────────────────────────────────────────────────
    def build_stats_embed(self, stats: dict, inventory: list) -> discord.Embed:
        embed = discord.Embed(title="📊 Tes stats et inventaire", color=discord.Color.blue())
        stats_text = "\n".join([f"{k.capitalize()}: {v}" for k, v in stats.items()])
        embed.add_field(name="🛡️ Stats", value=stats_text, inline=True)

        if inventory:
            inv_text = "\n".join([f"{item['nom']} ({item['effet']})" for item in inventory])
        else:
            inv_text = "Vide"
        embed.add_field(name="🎒 Inventaire", value=inv_text, inline=True)
        return embed

    # ────────────────────────────────────────────────────────────────────────────
    # 🧱 Création ou reprise de session
    # ────────────────────────────────────────────────────────────────────────────
    async def start_session(self, user: discord.User, channel: discord.TextChannel):
        active_players = supabase.table("players").select("*").execute().data
        if len(active_players) >= MAX_ACTIVE_PLAYERS and not any(p["discord_id"] == user.id for p in active_players):
            await safe_send(channel, "🚫 Trop de shinigamis actifs, réessaie plus tard.")
            return

        result = supabase.table("players").select("*").eq("discord_id", user.id).execute()
        player = result.data[0] if result.data else None

        if player:
            history = player["history"]
            stats = player.get("stats", {})
            inventory = player.get("inventory", [])
            save_state = player.get("save_state", {})
            await safe_send(channel, "🌫️ *Le vent du Néant souffle à nouveau...*")
            await safe_send(channel, embed=self.build_stats_embed(stats, inventory))
        else:
            history = [{"role": "system", "content": SYSTEM_PROMPT}]
            stats = {"pv": 100, "force": 10, "agilite": 8, "reiatsu": 15, "chance": 5}
            inventory = [{"nom": "Zanpakuto", "effet": "attaque +5"}]
            save_state = {"acte": 1, "choix_importants": [], "statut": "sain", "lieux_visites": [], "evenements": []}

            supabase.table("players").insert({
                "discord_id": user.id,
                "history": history,
                "last_channel": str(channel.id),
                "stats": stats,
                "inventory": inventory,
                "save_state": save_state
            }).execute()

            embed = self.build_intro_embed(user)
            await safe_send(channel, embed=embed)
            await safe_send(channel, embed=self.build_stats_embed(stats, inventory))

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

        # ──────────────
        # ⚡ Fin si PV <= 0
        # ──────────────
        if session["stats"].get("pv", 0) <= 0:
            await safe_send(message.channel, "💀 *Tes PV sont tombés à 0. L’aventure se termine...*")
            del self.sessions[user_id]
            supabase.table("players").delete().eq("discord_id", user_id).execute()
            return

        # ──────────────
        # 📝 Ajout du tour et mise à jour du cache
        # ──────────────
        session["history"].append({"role": "user", "content": mot})
        session["last_activity"] = datetime.utcnow()

        # ⚔️ Gestion simple des actions
        if mot.lower() == "attaque":
            degats = random.randint(5, 15) + session["stats"]["force"]
            session["stats"]["pv"] -= max(0, degats - session["stats"].get("agilite", 0)//2)
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
            session["save_state"]["evenements"].append(f"utilisé {item['nom']}")

        # ──────────────
        # 🔹 Appel GPT pour continuité narrative
        # ──────────────
        try:
            context = session["history"] + [{"role": "system", "content": f"Stats: {session['stats']}, Inventory: {session['inventory']}"}]
            response = await asyncio.to_thread(get_story_continuation, context)
        except Exception as e:
            await safe_send(message.channel, "⚠️ Le narrateur se tait...")
            print(f"[Erreur RPGPT] {e}")
            del self.sessions[user_id]
            return

        session["history"].append({"role": "assistant", "content": response})

        # ──────────────
        # 🔹 Mise à jour Supabase
        # ──────────────
        supabase.table("players").upsert({
            "discord_id": user_id,
            "history": session["history"],
            "stats": session["stats"],
            "inventory": session["inventory"],
            "save_state": session["save_state"],
            "last_channel": str(message.channel.id)
        }).execute()

        # ──────────────
        # 🔹 Envoi du récit + stats
        # ──────────────
        await safe_send(message.channel, response)
        await safe_send(message.channel, embed=self.build_stats_embed(session["stats"], session["inventory"]))

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = RPGPT(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
