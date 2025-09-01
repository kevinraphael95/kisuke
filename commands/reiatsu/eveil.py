# ────────────────────────────────────────────────────────────────────────────────
# 📌 eveil.py — Commande /eveil et !eveil
# Objectif : Choisir son éveil spirituel (Shinigami, Hollow, Quincy, Fullbring)
# Condition : Nécessite 300 reiatsu (consommés)
# Table : reiatsu2 (user_id, pouvoir)
# Catégorie : RPG
# Accès : Tous
# Cooldown : 1 / 30 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import aiosqlite
from utils.discord_utils import safe_send, safe_respond

POUVOIRS = ["Shinigami", "Hollow", "Quincy", "Fullbring"]

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class EveilCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_reiatsu(self, user_id: int):
        """Retourne le score de reiatsu du joueur."""
        async with aiosqlite.connect("database.db") as db:
            cur = await db.execute("SELECT reiatsu FROM reiatsu WHERE user_id = ?", (user_id,))
            row = await cur.fetchone()
            return row[0] if row else 0

    async def add_pouvoir(self, user_id: int, pouvoir: str):
        """Enregistre l'éveil du joueur dans reiatsu2."""
        async with aiosqlite.connect("database.db") as db:
            await db.execute("""
                INSERT INTO reiatsu2 (user_id, pouvoir)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET pouvoir = excluded.pouvoir
            """, (user_id, pouvoir))
            await db.commit()

    async def update_reiatsu(self, user_id: int, amount: int):
        """Met à jour le reiatsu après consommation."""
        async with aiosqlite.connect("database.db") as db:
            await db.execute("UPDATE reiatsu SET reiatsu = reiatsu - ? WHERE user_id = ?", (amount, user_id))
            await db.commit()

    async def _do_eveil(self, user: discord.User, pouvoir: str, channel: discord.abc.Messageable):
        reiatsu = await self.get_reiatsu(user.id)
        if reiatsu < 300:
            await safe_send(channel, f"❌ Yo {user.mention}, tu as besoin de **300 reiatsu** pour éveiller tes pouvoirs (il te manque {300 - reiatsu}).")
            return

        # Consommer le reiatsu et enregistrer l'éveil
        await self.update_reiatsu(user.id, 300)
        await self.add_pouvoir(user.id, pouvoir)

        embed = discord.Embed(
            title="🌌 Éveil Spirituel",
            description=f"{user.mention} a éveillé ses pouvoirs spirituels et est devenu **{pouvoir}** !",
            color=discord.Color.gold()
        )
        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # Slash command
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="eveil", description="Éveille tes pouvoirs spirituels (300 reiatsu requis).")
    @app_commands.describe(pouvoir="Choisis ton éveil spirituel")
    @app_commands.choices(pouvoir=[
        app_commands.Choice(name=p, value=p) for p in POUVOIRS
    ])
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: i.user.id)
    async def slash_eveil(self, interaction: discord.Interaction, pouvoir: app_commands.Choice[str]):
        await interaction.response.defer()
        await self._do_eveil(interaction.user, pouvoir.value, interaction.channel)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────────
    # Prefix command
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="eveil")
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    async def prefix_eveil(self, ctx: commands.Context, pouvoir: str = None):
        if not pouvoir or pouvoir.capitalize() not in POUVOIRS:
            await safe_send(ctx.channel, f"❌ Utilisation : `!eveil <{'|'.join(POUVOIRS)}>`")
            return
        await self._do_eveil(ctx.author, pouvoir.capitalize(), ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = EveilCog(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "RPG"
    await bot.add_cog(cog)
