# ────────────────────────────────────────────────────────────────
# 📌 kluboutside.py — Commande interactive !kluboutside / !ko
# Objectif : Afficher une question Klub Outside par numéro ou lister toutes les questions avec pagination
# Catégorie : Bleach
# Accès : Public
# ──────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ──────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View
import json
import os

from discord_utils import safe_send, safe_edit  # <-- import utils

# ──────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ──────────────────────────────────────────────────────────
KO_DATA_PATH = os.path.join("data", "ko.json")
KO_IMAGE_DIR = os.path.join("data", "koimages")

def load_data():
    with open(KO_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ──────────────────────────────────────────────────────────
# 🎛️ UI — Pagination interactive pour les questions KO
# ──────────────────────────────────────────────────────────
class KlubPaginator(View):
    def __init__(self, ctx, data):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.data = data
        self.keys = list(data["Questions"].keys())
        self.index = 0

    async def send_embed(self, interaction):
        key = self.keys[self.index]
        question = self.data["Questions"][key]

        embed = discord.Embed(
            title=f"📓 Question Klub Outside n°{key}",
            color=discord.Color.dark_green()
        )
        embed.add_field(name="📅 Date", value=question.get("date", "?"), inline=False)
        embed.add_field(name="❓ Question", value=question.get("question", "?"), inline=False)
        embed.add_field(name="💬 Réponse", value=question.get("réponse", "?"), inline=False)
        embed.set_footer(text=f"{self.index+1} / {len(self.keys)}")

        image = self._find_image_file(key)
        if image:
            file = discord.File(image, filename=os.path.basename(image))
            embed.set_image(url=f"attachment://{os.path.basename(image)}")
            await interaction.response.edit_message(embed=embed, view=self, attachments=[file])
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    def _find_image_file(self, key):
        for ext in ["png", "jpg", "jpeg", "webp"]:
            path = os.path.join(KO_IMAGE_DIR, f"ko{key}.{ext}")
            if os.path.exists(path):
                return path
        return None

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Tu ne peux pas interagir avec ceci.", ephemeral=True)
        if self.index > 0:
            self.index -= 1
            await self.send_embed(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Tu ne peux pas interagir avec ceci.", ephemeral=True)
        if self.index < len(self.keys) - 1:
            self.index += 1
            await self.send_embed(interaction)

# ──────────────────────────────────────────────────────────
# 🧠 Cog principal
# ──────────────────────────────────────────────────────────
class KlubOutside(commands.Cog):
    """
    Commande !kluboutside — Affiche une question Klub Outside par numéro ou l'ensemble des questions
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="kluboutside",
        aliases=["ko"],
        help="📓 Affiche une question Klub Outside par son numéro, ou pagine toutes si aucun numéro n'est donné.",
        description="Utilisation : `!ko [numéro]`"
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def kluboutside(self, ctx: commands.Context, numero: int = None):
        try:
            data = load_data()
            questions = data.get("Questions", {})

            # Si aucun argument : pagination
            if numero is None:
                view = KlubPaginator(ctx, data)
                embed = discord.Embed(
                    title=f"📓 Question Klub Outside n°1",
                    color=discord.Color.dark_green()
                )
                question = questions.get("1")
                embed.add_field(name="📅 Date", value=question.get("date", "?"), inline=False)
                embed.add_field(name="❓ Question", value=question.get("question", "?"), inline=False)
                embed.add_field(name="💬 Réponse", value=question.get("réponse", "?"), inline=False)
                embed.set_footer(text=f"1 / {len(questions)}")

                image_path = view._find_image_file("1")
                if image_path:
                    file = discord.File(image_path, filename=os.path.basename(image_path))
                    await safe_send(ctx.channel, embed=embed, view=view, file=file)
                else:
                    await safe_send(ctx.channel, embed=embed, view=view)
                return

            # Sinon, afficher question spécifique
            q = questions.get(str(numero))
            if not q:
                await safe_send(ctx.channel, f"❌ Aucune question trouvée pour le numéro {numero}.")
                return

            embed = discord.Embed(
                title=f"📓 Question Klub Outside n°{numero}",
                color=discord.Color.green()
            )
            embed.add_field(name="📅 Date", value=q.get("date", "?"), inline=False)
            embed.add_field(name="❓ Question", value=q.get("question", "?"), inline=False)
            embed.add_field(name="💬 Réponse", value=q.get("réponse", "?"), inline=False)

            for ext in ["png", "jpg", "jpeg", "webp"]:
                image_path = os.path.join(KO_IMAGE_DIR, f"ko{numero}.{ext}")
                if os.path.exists(image_path):
                    file = discord.File(image_path, filename=os.path.basename(image_path))
                    embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
                    await safe_send(ctx.channel, embed=embed, file=file)
                    return

            await safe_send(ctx.channel, embed=embed)

        except FileNotFoundError:
            await safe_send(ctx.channel, "❌ Le fichier `ko.json` est introuvable.")
        except Exception as e:
            await safe_send(ctx.channel, f"⚠️ Erreur : `{e}`")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = KlubOutside(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
