import random
import discord
from discord.ext import commands

class CouleurCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="couleur", help="Montre une couleur aléatoire.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown 3s
    async def couleur(self, ctx):
        # 🔵 Génère une couleur aléatoire (RGB et Hex)
        code_hex = random.randint(0, 0xFFFFFF)
        r = (code_hex >> 16) & 0xFF
        g = (code_hex >> 8) & 0xFF
        b = code_hex & 0xFF

        hex_str = f"#{code_hex:06X}"
        rgb_str = f"({r}, {g}, {b})"

        # 🖼️ Image de prévisualisation
        image_url = f"https://dummyimage.com/300x100/{code_hex:06x}/{code_hex:06x}.png&text=%20"

        # 📩 Embed affiché
        embed = discord.Embed(
            title="🎨 Couleur aléatoire",
            description=f"**Hex :** `{hex_str}`\n**RGB :** `{rgb_str}`",
            color=code_hex
        )
        embed.set_image(url=image_url)
        await ctx.send(embed=embed)

# 🔌 Chargement automatique + ajout de catégorie
async def setup(bot):
    cog = CouleurCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
