# ───────────────────────────────────────────────────────────────────────
# 📌 kido_command.py — Commande interactive !kido
# Objectif : Lancer un sort de Kidō avec animation et incantation
# Catégorie : Bleach
# Accès : Public
# ──────────────────────────────────────────────────────────────────

# ───────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ───────────────────────────────────────────────────
import discord
from discord.ext import commands
import json
import asyncio
import os

# Import des fonctions sécurisées pour éviter le rate-limit 429
from utils.discord_utils import safe_send, safe_edit  # <-- Import utils safe_send / safe_edit

# ───────────────────────────────────────────────────
# 📂 Chargement des données Kidō
# ───────────────────────────────────────────────────
KIDO_FILE = os.path.join("data", "kido.json")
def load_kido_data():
    with open(KIDO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ───────────────────────────────────────────────────
# 🔁 Paginator pour lister les sorts
# ───────────────────────────────────────────────────
class KidoPaginator(discord.ui.View):
    def __init__(self, ctx, pages):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.pages = pages
        self.index = 0

    async def update_message(self, interaction):
        embed = self.pages[self.index]
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Tu ne peux pas interagir avec cette pagination.", ephemeral=True)
        if self.index > 0:
            self.index -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("❌ Tu ne peux pas interagir avec cette pagination.", ephemeral=True)
        if self.index < len(self.pages) - 1:
            self.index += 1
            await self.update_message(interaction)

# ───────────────────────────────────────────────────
# 🧠 Cog principal
# ───────────────────────────────────────────────────
class Kido(commands.Cog):
    """
    Commande !kido — Lance un sort de Kidō avec animation et incantation.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="kido",
        help="🎼 Lance un sort de Kidō ! Syntaxe : `!!kido <type> <numéro>`",
        description="Exemple : `!!kido bakudo 61`"
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def kido(self, ctx, type_kido: str = None, numero: int = None):
        try:
            data = load_kido_data()

            # ➤ Aucun argument fourni → liste paginée des sorts
            if type_kido is None and numero is None:
                all_sorts = []
                for kido_type, sorts in data.items():
                    for sort in sorts:
                        all_sorts.append(f"`{kido_type.title()} {sort['numero']}` — {sort['nom']}")

                # Diviser la liste en pages de 20 éléments
                pages = []
                for i in range(0, len(all_sorts), 20):
                    embed = discord.Embed(
                        title="📘 Liste des sorts de Kidō",
                        description="\n".join(all_sorts[i:i+20]),
                        color=discord.Color.teal()
                    )
                    embed.set_footer(text=f"Page {i//20+1}/{(len(all_sorts)-1)//20+1}")
                    pages.append(embed)

                view = KidoPaginator(ctx, pages)
                await safe_send(ctx.channel, embed=pages[0], view=view)
                return

            # ➤ Argument fourni → comportement normal
            type_kido = type_kido.lower()
            if type_kido not in data:
                await safe_send(ctx.channel, f"❌ Type de Kidō inconnu : `{type_kido}`.")
                return

            sort = next((k for k in data[type_kido] if k["numero"] == numero), None)
            if not sort:
                await safe_send(ctx.channel, f"❌ Aucun sort {type_kido} numéro {numero} trouvé.")
                return

            nom = sort["nom"]
            incantation = sort.get("incantation")
            image = sort.get("image")

            # ⏳ Animation dramatique
            loading = await safe_send(ctx.channel, f"🤘 Concentration... (`{type_kido.title()} #{numero}`)")
            await asyncio.sleep(1.5)

            # 📈 Embed final
            embed = discord.Embed(
                title=f"{type_kido.title()} #{numero} — {nom}",
                color=discord.Color.purple()
            )
            embed.add_field(name="🎼 Sort lancé par", value=ctx.author.mention, inline=False)
            embed.add_field(name="📜 Incantation", value=f"*{incantation}*" if incantation else "*(Aucune incantation connue)*", inline=False)
            if image:
                embed.set_image(url=image)

            await safe_edit(loading, content=None, embed=embed)

        except FileNotFoundError:
            await safe_send(ctx.channel, "❌ Le fichier `kido.json` est introuvable.")
        except Exception as e:
            await safe_send(ctx.channel, f"⚠️ Erreur : `{e}`")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Kido(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
