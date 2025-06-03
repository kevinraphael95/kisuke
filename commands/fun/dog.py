# ────────────────────────────────────────────────────────────────────────────────
# 📌 dog_command.py — Commande interactive !dog
# Objectif : Afficher une image aléatoire de chien via une API publique
# Catégorie : 🎉 Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import aiohttp
import discord
from discord.ext import commands

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class DogCommand(commands.Cog):
    """
    Commande !dog — Affiche une photo aléatoire d’un chien.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="dog",
        help="🐶 Affiche une photo aléatoire d’un chien.",
        description="Utilise l'API Dog CEO pour afficher une image aléatoire de chien."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def dog(self, ctx: commands.Context):
        """Commande principale qui récupère et affiche une image de chien."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://dog.ceo/api/breeds/image/random") as response:
                    if response.status == 200:
                        data = await response.json()
                        image_url = data.get("message")
                        if image_url:
                            await ctx.send(f"Voici un toutou aléatoire ! 🐶\n{image_url}")
                        else:
                            await ctx.send("❌ L'API a répondu, mais pas d'image trouvée.")
                    else:
                        await ctx.send("❌ Impossible de récupérer une image de chien 😢")
        except Exception as e:
            print(f"[ERREUR dog] {e}")
            await ctx.send("❌ Une erreur est survenue lors de la récupération de l'image.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = DogCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
