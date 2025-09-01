# ────────────────────────────────────────────────────────────────────────────────
# 📌 eveil.py — Commande interactive /eveil et !eveil
# Objectif : Permet à un utilisateur de dépenser 300 reiatsu pour choisir un pouvoir
# Catégorie : RPG
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import aiosqlite

from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu de sélection du pouvoir
# ────────────────────────────────────────────────────────────────────────────────
class EveilView(View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=120)
        self.bot = bot
        self.user_id = user_id
        self.add_item(EveilButton("Shinigami", self))
        self.add_item(EveilButton("Hollow", self))
        self.add_item(EveilButton("Quincy", self))
        self.add_item(EveilButton("Fullbring", self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if hasattr(self, "message") and self.message:
            await safe_edit(self.message, view=self)

class EveilButton(Button):
    def __init__(self, pouvoir, parent_view):
        super().__init__(label=pouvoir, style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        try:
            # Vérifier les reiatsu de l'utilisateur
            async with aiosqlite.connect("data/reiatsu.db") as db:
                cursor = await db.execute("SELECT reiatsu FROM reiatsu WHERE user_id = ?", (self.parent_view.user_id,))
                row = await cursor.fetchone()
                if not row:
                    await safe_respond(interaction, "❌ Tu n'as pas de reiatsu enregistré.", ephemeral=True)
                    return
                reiatsu = row[0]
                if reiatsu < 300:
                    await safe_respond(interaction, "⛔ Tu n'as pas assez de reiatsu (300 requis).", ephemeral=True)
                    return

                # Déduire les 300 reiatsu
                await db.execute("UPDATE reiatsu SET reiatsu = reiatsu - 300 WHERE user_id = ?", (self.parent_view.user_id,))
                # Enregistrer le pouvoir
                await db.execute("INSERT OR REPLACE INTO reiatsu2(user_id, pouvoir) VALUES(?, ?)", (self.parent_view.user_id, self.label))
                await db.commit()

            embed = discord.Embed(
                title="✨ Éveil réussi !",
                description=f"Tu as choisi le pouvoir **{self.label}**.\n300 reiatsu ont été retirés.",
                color=discord.Color.green()
            )
            await safe_edit(interaction.message, content=None, embed=embed, view=None)

        except Exception as e:
            print(f"[ERREUR EveilButton] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Eveil(commands.Cog):
    """
    Commande /eveil et !eveil — Dépenser 300 reiatsu pour choisir un pouvoir
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_menu(self, channel: discord.abc.Messageable, user_id: int):
        view = EveilView(self.bot, user_id)
        view.message = await safe_send(channel, "Choisis ton pouvoir spirituel :", view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="eveil",
        description="Dépenser 300 reiatsu pour choisir un pouvoir spirituel"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_eveil(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._send_menu(interaction.channel, interaction.user.id)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /eveil] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="eveil")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_eveil(self, ctx: commands.Context):
        try:
            await self._send_menu(ctx.channel, ctx.author.id)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !eveil] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Eveil(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "RPG"
    await bot.add_cog(cog)
