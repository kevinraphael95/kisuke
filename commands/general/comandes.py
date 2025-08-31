# ────────────────────────────────────────────────────────────────────────────────
# 📌 commandes.py — Commande simple /commandes et !commandes
# Objectif : Affiche la liste de toutes les commandes et leurs descriptions
# Catégorie : Utilitaire
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

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Commandes(commands.Cog):
    """
    Commande /commandes et !commandes — Affiche la liste des commandes et descriptions
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne pour créer l'embed
    # ────────────────────────────────────────────────────────────────────────────
    def build_embed(self):
        embed = discord.Embed(
            title="📜 Liste des commandes",
            description="Voici toutes les commandes disponibles avec leurs descriptions :",
            color=discord.Color.blue()
        )
        # Regrouper par catégorie
        categories = {}
        for cmd in self.bot.commands:
            cat = getattr(cmd, "category", "Autre")
            if cat not in categories:
                categories[cat] = []
            desc = cmd.help if cmd.help else "Pas de description."
            categories[cat].append((cmd.name, desc))

        for cat, cmds in categories.items():
            value = "\n".join(f"**{name}** — {desc}" for name, desc in cmds)
            embed.add_field(name=f"📂 {cat}", value=value, inline=False)

        return embed

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="commandes",
        description="Affiche toutes les commandes disponibles avec leurs descriptions."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_commandes(self, interaction: discord.Interaction):
        try:
            embed = self.build_embed()
            await safe_respond(interaction, embed=embed)
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /commandes] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="commandes",
        help="Affiche toutes les commandes disponibles avec leurs descriptions."
    )
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_commandes(self, ctx: commands.Context):
        try:
            embed = self.build_embed()
            await safe_send(ctx.channel, embed=embed)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !commandes] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Commandes(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Utilitaire"
    await bot.add_cog(cog)
