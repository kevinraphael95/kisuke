# ────────────────────────────────────────────────────────────────────────────────
# 📌 confession.py — Commande interactive !confession
# Objectif : Envoyer anonymement un message à quelqu’un d’autre du serveur
# Catégorie : Test
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import asyncio
import re
from datetime import datetime, timedelta

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
confession_cooldowns = {}

class Confession(commands.Cog):
    """
    Commande !confession — Envoie anonymement un message à quelqu’un du serveur.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="confession",
        aliases=["confess", "cf"],
        help="Envoie anonymement un message à quelqu’un du serveur.",
        description="💌 Envoie anonymement un message à quelqu’un du serveur. Le destinataire le recevra en DM."
    )
    async def confession(self, ctx: commands.Context, target: discord.Member):
        """Commande principale pour envoyer une confession."""
        author = ctx.author

        if target.id == author.id:
            await ctx.send("❌ Tu ne peux pas t’envoyer une confession à toi-même.")
            return

        now = datetime.utcnow()
        if author.id in confession_cooldowns:
            cooldown_until = confession_cooldowns[author.id]
            if now < cooldown_until:
                delta = cooldown_until - now
                await ctx.send(f"⏳ Tu dois attendre encore {delta.seconds} secondes avant de refaire une confession.")
                return

        try:
            await author.send(f"💌 Tu veux envoyer une confession à **{target.display_name}**.\nEnvoie-moi ton message maintenant. Tu as 2 minutes.")
        except discord.Forbidden:
            await ctx.send("❌ Je n’ai pas pu t’envoyer de DM. Active-les pour utiliser cette commande.")
            return

        def check(m):
            return m.author.id == author.id and isinstance(m.channel, discord.DMChannel)

        try:
            msg = await self.bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            await author.send("⏳ Temps écoulé. Essaie de nouveau.")
            return

        content = msg.content.strip()

        if not content or re.search(r"@everyone|@here|<@!?[0-9]+>", content):
            await author.send("❌ Ton message contient une mention interdite ou est vide.")
            return

        try:
            await target.send(f"📨 **Quelqu’un t’a laissé une confession...**\n> {content}")
            await author.send("✅ Ta confession a été envoyée anonymement.")
            confession_cooldowns[author.id] = now + timedelta(seconds=10)
        except discord.Forbidden:
            await author.send("❌ Le destinataire a ses messages privés désactivés. La confession n’a pas pu être envoyée.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Confession(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
