# ────────────────────────────────────────────────────────────────────────────────
# 📌 motus.py — Commande interactive /motus et !motus
# Objectif : Jeu Motus interactif avec session individuelle et feedback emoji
# Catégorie : Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View
import random
import requests

# Utils sécurisés pour éviter erreurs 429 ou suppression ratée
from utils.discord_utils import safe_send, safe_edit, safe_respond, safe_delete  

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Motus(commands.Cog):
    """
    Commande /motus et !motus — Jeu Motus interactif
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions = {}  # {user_id: {"mot": str, "essais": int}}

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Choix d’un mot aléatoire
    # ────────────────────────────────────────────────────────────────────────────
    def get_random_word(self):
        """Récupère un mot aléatoire via API ou fallback local"""
        fallback_words = ["python", "discord", "motus", "bot", "fleur", "arbre", "maison", "chat", "chien", "soleil"]
        try:
            response = requests.get("https://random-word-api.herokuapp.com/word?length=6", timeout=5)
            if response.status_code == 200:
                return response.json()[0].lower()
        except:
            pass
        return random.choice(fallback_words)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Démarrer une partie
    # ────────────────────────────────────────────────────────────────────────────
    async def _start_game(self, channel: discord.abc.Messageable, user_id: int):
        mot = self.get_random_word()
        self.sessions[user_id] = {"mot": mot, "essais": 0}
        embed = discord.Embed(
            title="🎯 Motus !",
            description=f"Une nouvelle partie commence ! Devine le mot de **{len(mot)} lettres**.\nUtilise `!propose <mot>` pour jouer.",
            color=discord.Color.green()
        )
        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Proposer un mot
    # ────────────────────────────────────────────────────────────────────────────
    async def _propose(self, ctx: commands.Context, mot: str):
        user_id = ctx.author.id
        if user_id not in self.sessions:
            return await safe_send(ctx.channel, "❌ Tu n'as pas de partie en cours. Utilise `!motus` pour commencer.")

        session = self.sessions[user_id]
        target = session["mot"]
        session["essais"] += 1

        if len(mot) != len(target):
            return await safe_send(ctx.channel, f"⚠️ Le mot doit faire {len(target)} lettres.")

        # 🔹 Comparaison lettre par lettre
        result = []
        for i, l in enumerate(mot.lower()):
            if l == target[i]:
                result.append("✅")  # bien placé
            elif l in target:
                result.append("⚪")  # présent mais mal placé
            else:
                result.append("❌")  # absent

        embed = discord.Embed(
            title=f"Essai n°{session['essais']}",
            description=f"Mot proposé : **{mot}**\nRésultat : {''.join(result)}",
            color=discord.Color.orange()
        )
        await safe_send(ctx.channel, embed=embed)

        if mot.lower() == target:
            embed = discord.Embed(
                title="🎉 Bravo !",
                description=f"Tu as trouvé le mot **{target}** en {session['essais']} essais.",
                color=discord.Color.green()
            )
            await safe_send(ctx.channel, embed=embed)
            del self.sessions[user_id]
        elif session["essais"] >= 6:
            embed = discord.Embed(
                title="💀 Partie terminée",
                description=f"Le mot était **{target}**. Retente ta chance !",
                color=discord.Color.red()
            )
            await safe_send(ctx.channel, embed=embed)
            del self.sessions[user_id]

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH /motus
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="motus",
        description="Démarre une nouvelle partie de Motus."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_motus(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._start_game(interaction.channel, interaction.user.id)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s avant de réutiliser cette commande.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /motus] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX !motus
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="motus")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_motus(self, ctx: commands.Context):
        try:
            await self._start_game(ctx.channel, ctx.author.id)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s avant de réutiliser cette commande.")
        except Exception as e:
            print(f"[ERREUR !motus] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX !propose <mot>
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="propose")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_propose(self, ctx: commands.Context, mot: str):
        try:
            await self._propose(ctx, mot)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s avant de réutiliser cette commande.")
        except Exception as e:
            print(f"[ERREUR !propose] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Motus(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
