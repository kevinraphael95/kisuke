# ────────────────────────────────────────────────────────────────────────────────
# 📌 couleur.py — Commande interactive !couleur
# Objectif : Afficher une couleur aléatoire avec ses codes HEX et RGB dans un embed Discord
# Catégorie : 🎨 Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import random
import discord
from discord.ext import commands

from utils.discord_utils import safe_send, safe_edit  # ✅ Sécurité anti-429

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Vue interactive avec bouton "Nouvelle couleur"
# ────────────────────────────────────────────────────────────────────────────────
class CouleurView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

    def generer_embed(self):
        code_hex = random.randint(0, 0xFFFFFF)
        hex_str = f"#{code_hex:06X}"
        r = (code_hex >> 16) & 0xFF
        g = (code_hex >> 8) & 0xFF
        b = code_hex & 0xFF
        rgb_str = f"({r}, {g}, {b})"
        image_url = f"https://dummyimage.com/700x200/{code_hex:06x}/{code_hex:06x}.png&text=+"

        embed = discord.Embed(
            title="🌈 Couleur aléatoire",
            description=f"🔹 **Code HEX** : `{hex_str}`\n🔸 **Code RGB** : `{rgb_str}`",
            color=code_hex
        )
        embed.set_image(url=image_url)
        return embed

    @discord.ui.button(label="🔁 Nouvelle couleur", style=discord.ButtonStyle.primary)
    async def regenerate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("❌ Tu ne peux pas utiliser ce bouton.", ephemeral=True)
            return

        try:
            new_embed = self.generer_embed()
            await safe_edit(interaction.message, embed=new_embed, view=self)
            await interaction.response.defer()
        except Exception as e:
            await safe_edit(interaction, content=f"❌ Erreur : {e}", view=None)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CouleurCommand(commands.Cog):
    """
    Commande !couleur — Génère et affiche une couleur aléatoire avec codes HEX et RGB.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="couleur",
        help="🎨 Affiche une couleur aléatoire avec ses codes HEX et RGB.",
        description="Affiche une couleur aléatoire avec un aperçu visuel et ses codes HEX & RGB."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def couleur(self, ctx: commands.Context):
        """Commande principale générant une couleur aléatoire."""
        try:
            view = CouleurView(ctx.author)
            embed = view.generer_embed()
            embed.timestamp = ctx.message.created_at
            await safe_send(ctx, embed=embed, view=view)
        except Exception as e:
            await safe_send(ctx, f"❌ Une erreur est survenue : `{e}`")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CouleurCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
