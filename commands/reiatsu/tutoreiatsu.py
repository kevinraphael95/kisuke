# ────────────────────────────────────────────────────────────────────────────────
# 📌 tutoreiatsu.py — Commande !tutoreiatsu /tutoreiatsu (aliases : tutorts, help rts)
# Objectif : Tutoriel interactif expliquant le système Reiatsu et ses fonctionnalités
# Catégorie : Reiatsu
# Accès : Public
# Cooldown : 1 utilisation / 30 secondes / utilisateur
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
class TutoReiatsu(commands.Cog):
    """
    Commande !tutoreiatsu ou /tutoreiatsu — Tutoriel sur le système Reiatsu
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_tutoriel(self, channel: discord.abc.Messageable, user: discord.abc.User):
        embed = discord.Embed(
            title="📖 Tutoriel Reiatsu",
            description="Bienvenue dans le système **Reiatsu** ! Voici tout ce que tu dois savoir pour progresser 👇",
            color=discord.Color.blurple()
        )

        # Explication Reiatsu
        embed.add_field(
            name="💠 Reiatsu — L’énergie principale",
            value=(
                "• Tu gagnes du **Reiatsu** en collectant les orbes qui apparaissent aléatoirement.\n"
                "• Les orbes peuvent être **normaux (+1)** ou **super (+100)**.\n"
                "• Plus tu en accumules, plus tu montes dans le classement."
            ),
            inline=False
        )

        # Explication Classes
        embed.add_field(
            name="🎭 Les Classes",
            value=(
                "• Tu peux choisir une **classe** avec `/classe`.\n"
                "• Chaque classe a :\n"
                "  🔹 Une **compétence passive** (toujours active).\n"
                "  🔹 Une **compétence active** utilisable avec `/skill` (soumise à cooldown).\n"
                "👉 Exemple : **Voleur 🥷** a plus de chances de réussir ses vols et peut garantir un vol avec `/skill`."
            ),
            inline=False
        )

        # Explication Skills
        embed.add_field(
            name="⚡ Compétences actives",
            value=(
                "• Utilise `/skill` pour activer la compétence spéciale de ta classe.\n"
                "• Chaque compétence a un **cooldown** (8h ou 12h en général).\n"
                "• Exemples :\n"
                "  🌀 Absorbeur → Le prochain Reiatsu est garanti en **super (+100)**.\n"
                "  🎲 Parieur → Mise 10 Reiatsu pour tenter d’en gagner 30."
            ),
            inline=False
        )

        # Explication Vol
        embed.add_field(
            name="🥷 Vol de Reiatsu",
            value=(
                "• Tu peux voler du Reiatsu aux autres avec `/reiatsuvol @pseudo`.\n"
                "• Chance de base : **25%** de réussir.\n"
                "• Les classes influencent ce taux (ex : Voleur → 67%).\n"
                "• Si tu rates, tu subis un cooldown avant de retenter."
            ),
            inline=False
        )

        # Explication KeyLottery
        embed.add_field(
            name="🎟️ Loterie Reiatsu (Clés Steam)",
            value=(
                "• Avec `/keylottery`, tu peux acheter un **ticket à gratter** (250 Reiatsu).\n"
                "• Clique sur un des 10 boutons pour tenter ta chance :\n"
                "  🔑 Gagne une **clé Steam** 🎮\n"
                "  💎 Gagne le **double de ta mise**\n"
                "  ❌ Ou... rien du tout 😢"
            ),
            inline=False
        )

        # Commandes utiles
        embed.add_field(
            name="📌 Commandes principales",
            value=(
                "`/reiatsu` → Voir ton profil\n"
                "`/classe` → Choisir ta classe\n"
                "`/skill` → Activer ta compétence\n"
                "`/reiatsuvol` → Voler du Reiatsu\n"
                "`/keylottery` → Jouer au ticket à gratter\n"
                "`/tutoreiatsu` → Réafficher ce tutoriel"
            ),
            inline=False
        )

        embed.set_footer(text="🌌 Reiatsu System • Reste actif pour progresser et débloquer des clés Steam !")

        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande prefix
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="tutoreiatsu", aliases=["tutorts", "helprts"], help="Tutoriel complet sur le système Reiatsu")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def prefix_tutoreiatsu(self, ctx: commands.Context):
        await self._send_tutoriel(ctx.channel, ctx.author)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande slash
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="tutoreiatsu", description="Tutoriel complet sur le système Reiatsu")
    @app_commands.checks.cooldown(1, 30, key=lambda i: i.user.id)
    async def slash_tutoreiatsu(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._send_tutoriel(interaction.channel, interaction.user)
        try:
            await interaction.delete_original_response()
        except discord.Forbidden:
            pass

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TutoReiatsu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
