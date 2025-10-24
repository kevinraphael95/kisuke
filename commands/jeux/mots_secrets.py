# ────────────────────────────────────────────────────────────────────────────────
# 📌 motssecrets.py — Jeu des Mots Secrets multijoueur
# Objectif : Pendant 3 minutes, tout le monde peut proposer un mot secret pour gagner du Reiatsu
# Catégorie : Jeux / Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond
from utils.supabase_client import supabase
import json
from pathlib import Path
from datetime import datetime, timedelta
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
MOTS_PATH = Path("data/motssecrets.json")
with MOTS_PATH.open("r", encoding="utf-8") as f:
    MOTS = json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class MotsSecretsMulti(commands.Cog):
    """
    🎮 Jeu des Mots Secrets Multijoueur — Pendant 3 minutes, proposez des mots pour gagner du Reiatsu !
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_games = {}  # channel_id : end_time

    # ────────────────────────────────────────────────────────────
    # 🔧 Méthodes internes
    # ────────────────────────────────────────────────────────────
    def normalize(self, text: str) -> str:
        return text.strip().lower()

    async def start_game(self, channel: discord.TextChannel):
        """Démarre un nouveau jeu de 3 minutes dans le channel."""
        if channel.id in self.active_games:
            await safe_send(channel, "⚠️ Un jeu est déjà en cours ici !")
            return

        self.active_games[channel.id] = datetime.utcnow() + timedelta(minutes=3)

        embed = discord.Embed(
            title="📝 Jeu des Mots Secrets !",
            description=(
                "💡 Il y a 100 mots secret à trouver, un mot trouvé rapporte 10 reiatsu une fois par personne. "
                "Pendant **3 minutes**, proposez autant de mots que vous voulez en mettant`.` ou `*` devant.\n"
                "Exemple : `.exemple` ou `*exemple`\n\n"
                "🎯 Si le mot proposé n'est pas un mot secret le bot ne répond pas.\n"
                "⚠️ Si c'est un mot que vous aviez déjà trouvé, le bot vous le signalera.\n"
                "Bonne chance !"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="⏳ Le jeu se terminera automatiquement dans 3 minutes.")
        await safe_send(channel, embed=embed)

        # Fin automatique après 3 minutes
        async def stop_later():
            await asyncio.sleep(180)
            if channel.id in self.active_games:
                await safe_send(channel, "⏰ Le jeu des mots secrets est terminé !")
                del self.active_games[channel.id]

        asyncio.create_task(stop_later())

    async def handle_guess(self, message: discord.Message):
        """Gère la vérification d’un mot proposé."""
        mot_propose = self.normalize(message.content[1:])
        mot_data = [m for m in MOTS if self.normalize(m["mot"]) == mot_propose]
        if not mot_data:
            return  # mot inconnu

        mot_id = mot_data[0]["id"]
        user_id = message.author.id
        username = str(message.author)

        # Récupère les mots déjà trouvés
        user_data = supabase.table("mots_trouves").select("*").eq("user_id", user_id).execute()
        if user_data.data:
            mots_trouves = user_data.data[0].get("mots") or []
            if isinstance(mots_trouves, str):
                mots_trouves = json.loads(mots_trouves)
        else:
            mots_trouves = []

        if mot_id in mots_trouves:
            await message.reply(f"⚠️ {message.author.mention}, tu as déjà trouvé ce mot secret !")
            return

        # Ajoute le mot trouvé
        mots_trouves.append(mot_id)
        if user_data.data:
            supabase.table("mots_trouves").update({
                "mots": mots_trouves,
                "last_found_at": datetime.utcnow().isoformat()
            }).eq("user_id", user_id).execute()
        else:
            supabase.table("mots_trouves").insert({
                "user_id": user_id,
                "username": username,
                "mots": mots_trouves
            }).execute()

        # Donne 10 Reiatsu
        reiatsu_data = supabase.table("reiatsu").select("*").eq("user_id", user_id).execute()
        if reiatsu_data.data:
            points = reiatsu_data.data[0].get("points") or 0
            supabase.table("reiatsu").update({"points": points + 10}).eq("user_id", user_id).execute()
        else:
            supabase.table("reiatsu").insert({
                "user_id": user_id,
                "username": username,
                "points": 10
            }).execute()

        await message.reply(f"✅ Bravo {message.author.mention} ! Tu as trouvé un mot secret et gagnes **10 Reiatsu** 🎉")

    # ────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────
    @app_commands.command(
        name="motsecret",
        description="Pendant 3 minutes, cherchez l'un des 100 mots secrets pour gagner 10 Reiatsu."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_motsecret(self, interaction: discord.Interaction):
        await self.start_game(interaction.channel)
        await safe_respond(interaction, "✅ Jeu des mots secrets lancé dans ce salon !")

    # ────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────
    @commands.command(name="motsecret", aliases=["motssecrets", "ms"], help="Pendant 3 minutes, cherchez l'un des 100 mots secrets pour gagner 10 Reiatsu.")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_motsecret(self, ctx: commands.Context):
        await self.start_game(ctx.channel)

    # ────────────────────────────────────────────────────────────
    # 🎧 Événement : Proposition de mot
    # ────────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.id not in self.active_games:
            return
        if not (message.content.startswith(".") or message.content.startswith("*")):
            return
        mot_propose = message.content[1:]
        if not mot_propose.strip():
            return  # ignore les messages comme "." ou "*"
        await self.handle_guess(message)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MotsSecretsMulti(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
