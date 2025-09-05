# ────────────────────────────────────────────────────────────────────────────────
# 📌 motus.py — Jeu interactif Motus /motus et !motus
# Objectif : Jouer au jeu Motus façon télé avec grille colorée et mot aléatoire
# Catégorie : Fun
# Accès : Tous
# Cooldown : 1 utilisation / 30 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

# Utils sécurisés pour éviter erreurs 429
from utils.discord_utils import safe_send, safe_respond, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Liste de mots possibles
# ────────────────────────────────────────────────────────────────────────────────
WORDS = [
    "piano", "chat", "maison", "arbre", "porte", "bouteille", "fleur", "soleil", "lune", "village"
]

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Motus(commands.Cog):
    """
    Commande /motus et !motus — Jeu Motus interactif façon télé
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne : vérifier le mot et créer la ligne colorée
    # ────────────────────────────────────────────────────────────────────────────
    def create_feedback_line(self, guess: str, target: str) -> str:
        """Retourne la ligne du mot avec des blocs colorés."""
        line = []
        for i, c in enumerate(guess):
            if i < len(target) and c == target[i]:
                line.append(f"🟩{c.upper()}🟩")  # Correct et bien placé
            elif c in target:
                line.append(f"🟨{c.upper()}🟨")  # Présent mais mal placé
            else:
                line.append(f"⬛{c.upper()}⬛")  # Absente
        return ' '.join(line)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne : jouer Motus
    # ────────────────────────────────────────────────────────────────────────────
    async def play_game(self, channel: discord.abc.Messageable, author: discord.User):
        word = random.choice(WORDS).lower()
        max_attempts = 6
        attempts = 0
        lines = []

        embed = discord.Embed(
            title="🎯 Motus - Devine le mot !",
            description=f"Mot de {len(word)} lettres.",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Joueur : {author.display_name} | Essais restants : {max_attempts - attempts}")
        game_message = await safe_send(channel, embed=embed)

        def check(m):
            return m.author == author and m.channel == channel and len(m.content) == len(word)

        while attempts < max_attempts:
            try:
                guess_msg = await self.bot.wait_for('message', check=check, timeout=60.0)
                guess = guess_msg.content.lower()

                line = self.create_feedback_line(guess, word)
                lines.append(line)
                attempts += 1

                # Mise à jour de l'embed avec toutes les lignes
                embed.clear_fields()
                for idx, l in enumerate(lines, 1):
                    embed.add_field(name=f"Essai {idx}", value=l, inline=False)
                embed.set_footer(text=f"Joueur : {author.display_name} | Essais restants : {max_attempts - attempts}")

                await safe_edit(game_message, embed=embed)

                if guess == word:
                    embed.color = discord.Color.green()
                    embed.title = f"🎉 Bravo {author.display_name} ! Tu as trouvé le mot !"
                    await safe_edit(game_message, embed=embed)
                    return

            except asyncio.TimeoutError:
                embed.color = discord.Color.red()
                embed.title = f"⏰ Temps écoulé ! Le mot était **{word.upper()}**"
                await safe_edit(game_message, embed=embed)
                return

        # Si échec complet
        embed.color = discord.Color.red()
        embed.title = f"❌ Plus d'essais ! Le mot était **{word.upper()}**"
        await safe_edit(game_message, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="motus",
        description="Joue au jeu Motus façon télé et devine le mot !"
    )
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: (i.user.id))
    async def slash_motus(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self.play_game(interaction.channel, interaction.user)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s avant de rejouer.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /motus] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="motus")
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    async def prefix_motus(self, ctx: commands.Context):
        try:
            await self.play_game(ctx.channel, ctx.author)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s avant de rejouer.")
        except Exception as e:
            print(f"[ERREUR !motus] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Motus(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
