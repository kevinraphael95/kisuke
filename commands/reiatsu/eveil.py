# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select

import sqlite3

from utils.discord_utils import safe_send, safe_edit, safe_respond  # ✅ tes sécurités anti-429

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu de sélection des pouvoirs
# ────────────────────────────────────────────────────────────────────────────────
POUVOIRS = ["Shinigami", "Hollow", "Quincy", "Fullbring"]

class PouvoirSelectView(View):
    def __init__(self, cog, user_id: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id
        self.message = None
        self.add_item(PouvoirSelect(self))

    async def on_timeout(self):
        """Désactive le menu après expiration."""
        for child in self.children:
            child.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)


class PouvoirSelect(Select):
    def __init__(self, parent_view: PouvoirSelectView):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=pouvoir, value=pouvoir) for pouvoir in POUVOIRS]
        super().__init__(placeholder="Choisis ton pouvoir spirituel :", options=options)

    async def callback(self, interaction: discord.Interaction):
        choix = self.values[0]
        result = await self.parent_view.cog._do_eveil(interaction.user.id, choix)

        await safe_edit(
            interaction.message,
            content=result,
            embed=None,
            view=None
        )

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Eveil(commands.Cog):
    """
    Commande /eveil et !eveil — Permet d’éveiller ses pouvoirs spirituels
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne : gestion BDD
    # ────────────────────────────────────────────────────────────────────────────
    async def _do_eveil(self, user_id: int, pouvoir: str) -> str:
        """Vérifie la BDD et applique l’éveil si possible."""

        # Connexion
        conn = sqlite3.connect("data/reiatsu.db")
        cursor = conn.cursor()

        # Création table si elle n’existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reiatsu2 (
                user_id INTEGER PRIMARY KEY,
                pouvoir TEXT
            )
        """)

        # Vérifie le reiatsu actuel dans la table principale
        cursor.execute("SELECT reiatsu FROM reiatsu WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return "❌ Tu n’as pas encore de reiatsu enregistré."

        reiatsu_actuel = row[0]
        if reiatsu_actuel < 300:
            conn.close()
            return f"⛔ Il te faut **300 reiatsu** pour éveiller un pouvoir. Actuel : {reiatsu_actuel}."

        # Déduit 300 et enregistre l’éveil
        cursor.execute("UPDATE reiatsu SET reiatsu = reiatsu - 300 WHERE user_id = ?", (user_id,))
        cursor.execute("INSERT OR REPLACE INTO reiatsu2 (user_id, pouvoir) VALUES (?, ?)", (user_id, pouvoir))
        conn.commit()
        conn.close()

        return f"🌌 Tu as éveillé ton pouvoir spirituel : **{pouvoir}** ! (-300 reiatsu)"

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Envoi du menu
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_menu(self, channel: discord.abc.Messageable, user_id: int):
        """Envoie le menu interactif pour choisir le pouvoir."""
        view = PouvoirSelectView(self, user_id)
        view.message = await safe_send(channel, "✨ Choisis ton éveil spirituel :", view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="eveil", description="Éveille tes pouvoirs spirituels (300 reiatsu requis).")
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: i.user.id)  # ⏳ Cooldown 30s
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
    @commands.cooldown(1, 30.0, commands.BucketType.user)  # ⏳ Cooldown 30s
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
            command.category = "Reiatsu"
    await bot.add_cog(cog)
