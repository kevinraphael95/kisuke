# ────────────────────────────────────────────────────────────────────────────────
# 📌 eveil.py — Commande /eveil et !eveil
# Objectif : Choisir son éveil spirituel (Shinigami, Hollow, Quincy, Fullbring)
# Condition : Nécessite 300 reiatsu (consommés)
# Table : reiatsu2 (user_id, pouvoir)
# Catégorie : Reiatsu
# Accès : Tous
# Cooldown : 1 / 30 secondes / utilisateur
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
# 🎛️ UI — Boutons
# ────────────────────────────────────────────────────────────────────────────────
POUVOIRS = ["Shinigami", "Hollow", "Quincy", "Fullbring"]

class PouvoirButton(Button):
    def __init__(self, parent_view, pouvoir: str):
        super().__init__(label=pouvoir, style=discord.ButtonStyle.primary)
        self.parent_view = parent_view
        self.pouvoir = pouvoir

    async def callback(self, interaction: discord.Interaction):
        # ⚡ Appel async de la BDD pour éviter "interaction failed"
        result = await self.parent_view.cog._do_eveil(interaction.user.id, self.pouvoir)
        for child in self.parent_view.children:
            child.disabled = True
        await safe_edit(interaction.message, content=None, embed=discord.Embed(
            title="🌌 Éveil Spirituel",
            description=result,
            color=discord.Color.gold()
        ), view=self.parent_view)

class PouvoirView(View):
    def __init__(self, cog):
        super().__init__(timeout=60)
        self.cog = cog
        for pouvoir in POUVOIRS:
            self.add_item(PouvoirButton(self, pouvoir))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if hasattr(self, 'message') and self.message:
            await safe_edit(self.message, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Eveil(commands.Cog):
    """Commande /eveil et !eveil — Permet d’éveiller ses pouvoirs spirituels"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🔹 Fonction interne pour gérer l'éveil (async)
    async def _do_eveil(self, user_id: int, pouvoir: str) -> str:
        async with aiosqlite.connect("data/reiatsu.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reiatsu2 (
                    user_id INTEGER PRIMARY KEY,
                    pouvoir TEXT
                )
            """)
            async with db.execute("SELECT reiatsu FROM reiatsu WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
            if not row:
                return "❌ Tu n’as pas encore de reiatsu enregistré."
            if row[0] < 300:
                return f"⛔ Il te faut **300 reiatsu** pour éveiller un pouvoir. Actuel : {row[0]}."
            await db.execute("UPDATE reiatsu SET reiatsu = reiatsu - 300 WHERE user_id = ?", (user_id,))
            await db.execute("INSERT OR REPLACE INTO reiatsu2 (user_id, pouvoir) VALUES (?, ?)", (user_id, pouvoir))
            await db.commit()
            return f"🌌 Tu as éveillé ton pouvoir spirituel : **{pouvoir}** ! (-300 reiatsu)"

    # 🔹 Envoi du menu interactif
    async def _send_menu(self, channel: discord.abc.Messageable):
        view = PouvoirView(self)
        view.message = await safe_send(channel, "✨ Choisis ton pouvoir spirituel :", view=view)

    # 🔹 Commande slash
    @app_commands.command(name="eveil", description="Éveille tes pouvoirs spirituels (300 reiatsu requis).")
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: i.user.id)
    async def slash_eveil(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._send_menu(interaction.channel)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /eveil] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # 🔹 Commande préfixe
    @commands.command(name="eveil")
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    async def prefix_eveil(self, ctx: commands.Context):
        try:
            await self._send_menu(ctx.channel)
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
