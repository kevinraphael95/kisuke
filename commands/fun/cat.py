# ────────────────────────────────────────────────────────────────────────────────
# 📌 cat.py — Commande interactive !cat
# Objectif : Afficher une photo de chat aléatoire depuis l'API Cataas
# Catégorie : Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import aiohttp  # 📡 Pour faire une requête HTTP
import io       # 📁 Pour manipuler les données d’image en mémoire

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CatCommand(commands.Cog):
    """
    Commande !cat — Affiche une photo de chat mignon aléatoire depuis l'API Cataas.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot  # 🔌 Référence à l’instance du bot

    @commands.command(
        name="cat",
        help="Affiche une photo de chat mignon."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 Anti-spam : 3s
    async def cat(self, ctx: commands.Context):
        """Commande principale pour afficher une image de chat aléatoire."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://cataas.com/cat") as response:
                    if response.status == 200:
                        image_data = await response.read()
                        image_file = discord.File(io.BytesIO(image_data), filename="cat.jpg")
                        await ctx.send("Voici un minou aléatoire ! 🐱", file=image_file)
                    else:
                        await ctx.send("😿 Impossible de récupérer une image de chat (API indisponible).")
            except Exception as e:
                await ctx.send(f"🚨 Une erreur est survenue : `{e}`")

    def cog_load(self):
        self.cat.category = "Fun"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(CatCommand(bot))
    print("✅ Cog chargé : CatCommand (catégorie = Fun)")
