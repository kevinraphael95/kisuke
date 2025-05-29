# ──────────────────────────────────────────────────────────────
# CAT
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import aiohttp  # 📡 Pour faire une requête HTTP
import io       # 📁 Pour manipuler les données d’image en mémoire

# ──────────────────────────────────────────────────────────────
# 🎮 COG : CatCommand — Envoie une image de chat random
# ──────────────────────────────────────────────────────────────
class CatCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # 🔌 Référence à l’instance du bot

    # ──────────────────────────────────────────────────────────
    # 📦 COMMANDE : !cat
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="cat",
        help="Affiche une photo de chat mignon."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 Anti-spam : 3s
    async def cat(self, ctx: commands.Context):
        # 🐾 Création d’une session HTTP pour appeler l’API Cataas
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://cataas.com/cat") as response:
                    # ✅ Si réponse OK (200), on lit l’image
                    if response.status == 200:
                        image_data = await response.read()
                        image_file = discord.File(io.BytesIO(image_data), filename="cat.jpg")

                        # 💌 Envoie le fichier avec un petit message
                        await ctx.send("Voici un minou aléatoire ! 🐱", file=image_file)
                    else:
                        # ⚠️ Erreur de statut HTTP (API down, etc.)
                        await ctx.send("😿 Impossible de récupérer une image de chat (API indisponible).")
            except Exception as e:
                # 🧨 Catch toute autre erreur
                await ctx.send(f"🚨 Une erreur est survenue : `{e}`")

    # 🏷️ Ajout dans la catégorie "Fun" pour le !help
    def cog_load(self):
        self.cat.category = "Fun"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(CatCommand(bot))
    print("✅ Cog chargé : CatCommand (catégorie = Fun)")
