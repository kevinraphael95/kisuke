# ────────────────────────────────────────────────────────────────────────────────
# 📌 pseudoabsurde.py — Commande interactive !pseudoabsurde
# Objectif : Modifier ton pseudo pour un format absurde avec deux adjectifs
# Catégorie : VAACT
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import random

# ────────────────────────────────────────────────────────────────────────────────
# 🎲 Liste d’adjectifs absurdes
# ────────────────────────────────────────────────────────────────────────────────
ADJECTIFS_ABSURDES = [
    "mature", "sérieux", "posé", "cohérent", "maîtrisé", "équilibré",
    "respectable", "lucide", "professionnel", "logique", "digne", "pondéré"
]

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class PseudoAbsurde(commands.Cog):
    """
    Commande !pseudoabsurde — Change ton pseudo pour un titre absurde
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="randompseudo",
        aliases=["ranpseudo"],
        help="Change ton pseudo en un format absurde (ex: Kevin l’homme mature et posé).",
        description="Génère un pseudo absurde basé sur ton prénom actuel et deux adjectifs choisis aléatoirement."
    )
    async def pseudoabsurde(self, ctx: commands.Context):
        """Commande principale pour changer le pseudo de manière absurde."""
        try:
            if not ctx.guild:
                await ctx.send("❌ Cette commande ne peut être utilisée qu’en serveur.")
                return

            member = ctx.author

            if not ctx.guild.me.guild_permissions.manage_nicknames:
                await ctx.send("❌ Je n’ai pas la permission de modifier les pseudos.")
                return

            prenom = member.nick if member.nick else member.name

            genre = "l’adulte"

            # Choix aléatoire d’adjectifs
            adj1, adj2 = random.sample(ADJECTIFS_ABSURDES, 2)

            nouveau_pseudo = f"{prenom} {genre} {adj1} et {adj2}"

            await member.edit(nick=nouveau_pseudo)

            await ctx.send(f"✅ Ton nouveau pseudo est maintenant : **{nouveau_pseudo}**")

        except discord.Forbidden:
            await ctx.send("❌ Je n’ai pas les permissions nécessaires pour modifier ton pseudo.")
        except Exception as e:
            print(f"[ERREUR pseudoabsurde] {e}")
            await ctx.send("❌ Une erreur est survenue en changeant ton pseudo.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = PseudoAbsurde(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "VAACT"
    await bot.add_cog(cog)
