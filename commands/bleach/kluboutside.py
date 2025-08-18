# ────────────────────────────────────────────────────────────────
# 📌 kluboutside.py — Commande interactive !kluboutside / !ko
# Objectif : Afficher une question Klub Outside par numéro, aléatoire ou paginer toutes
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
import random  # ← Ajouté

from utils.discord_utils import safe_send, safe_edit  # Utils anti rate-limit

# ──────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ──────────────────────────────────────────────────────────
KO_DATA_PATH = os.path.join("data", "ko.json")
KO_IMAGE_DIR = os.path.join("data", "images", "kluboutside")

def load_data():
    with open(KO_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ──────────────────────────────────────────────────────────
# 🎛️ UI — Pagination interactive
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
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])

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

    @discord.ui.button(label="🔀 Aléatoire", style=discord.ButtonStyle.primary)
    async def random_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Tu ne peux pas interagir avec ceci.", ephemeral=True)
        self.index = random.randint(0, len(self.keys) - 1)
        await self.send_embed(interaction)

# ──────────────────────────────────────────────────────────
# 🧠 Cog principal
# ──────────────────────────────────────────────────────────
class KlubOutside(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="kluboutside",
        aliases=["ko"],
        help="📓 Affiche une question de la FAQ du Klub Outside.",
        description="Utilisation : `!ko`, `!ko <numéro>`, `!ko random`"
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def kluboutside(self, ctx: commands.Context, *, argument: str = None):
        try:
            data = load_data()
            questions = data.get("Questions", {})
            keys = list(questions.keys())

            # Déterminer l'index de départ
            if argument is None:
                start_index = 0
            elif argument.lower() == "random":
                start_index = random.randint(0, len(keys) - 1)
            elif argument.isdigit():
                numero = argument
                if numero not in keys:
                    await safe_send(ctx.channel, f"❌ Aucune question trouvée pour le numéro {numero}.")
                    return
                start_index = keys.index(numero)
            else:
                await safe_send(ctx.channel, f"❌ Argument non reconnu : `{argument}`. Utilise un numéro ou `random`.")
                return

            # Lancer la vue de pagination depuis l'index choisi
            view = KlubPaginator(ctx, data)
            view.index = start_index
            key = view.keys[start_index]
            question = questions[key]

            embed = discord.Embed(
                title=f"📓 Question Klub Outside n°{key}",
                color=discord.Color.dark_green()
            )
            embed.add_field(name="📅 Date", value=question.get("date", "?"), inline=False)
            embed.add_field(name="❓ Question", value=question.get("question", "?"), inline=False)
            embed.add_field(name="💬 Réponse", value=question.get("réponse", "?"), inline=False)
            embed.set_footer(text=f"{start_index+1} / {len(view.keys)}")

            image_path = view._find_image_file(key)
            if image_path:
                embed.set_image(url=f"attachment://{os.path.basename(image_path)}")
                file = discord.File(image_path, filename=os.path.basename(image_path))
                await safe_send(ctx.channel, embed=embed, view=view, file=file)
            else:
                await safe_send(ctx.channel, embed=embed, view=view)

        except FileNotFoundError:
            await safe_send(ctx.channel, "❌ Le fichier `ko.json` est introuvable.")
        except Exception as e:
            await safe_send(ctx.channel, f"⚠️ Erreur : `{e}`")

# ──────────────────────────────────────────────────────────
# 🔌 Chargement du cog
# ──────────────────────────────────────────────────────────
async def setup(bot):
    cog = KlubOutside(bot)
    for command in cog.get_commands():
        command.category = "Bleach"
    await bot.add_cog(cog)
