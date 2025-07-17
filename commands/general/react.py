# ────────────────────────────────────────────────────────────────────────────────
# 📌 react.py — Commande !react
# Objectif : Réagit à un message avec un emoji animé temporaire
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from utils.discord_utils import safe_send
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReactCommand(commands.Cog):
    """
    Commande !react — Réagit à un message avec un emoji animé, puis le retire
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="react",
        aliases=["r"],
        help="Réagit à un message avec un emoji animé, puis le retire après 3 minutes.",
        description="Utilise un emoji animé du serveur pour réagir temporairement à un message précédent ou répondu."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def react(self, ctx: commands.Context, emoji_name: str):
        """Commande principale !react"""

        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass  # Ignore la suppression

        emoji_name_cleaned = emoji_name.strip(":").lower()

        # Recherche l'emoji animé correspondant
        emoji = next(
            (e for e in ctx.guild.emojis if e.animated and e.name.lower() == emoji_name_cleaned),
            None
        )
        if not emoji:
            await safe_send(ctx.channel, f"❌ Emoji animé `:{emoji_name_cleaned}:` introuvable sur ce serveur.", delete_after=5)
            return

        target_message = None

        # Si la commande répond à un message
        if ctx.message.reference:
            try:
                target_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except discord.NotFound:
                await safe_send(ctx.channel, "❌ Message référencé introuvable.", delete_after=5)
                return
        else:
            # Sinon, cherche le dernier message avant la commande
            async for msg in ctx.channel.history(limit=20, before=ctx.message.created_at):
                if msg.id != ctx.message.id:
                    target_message = msg
                    break

        if not target_message or target_message.id == ctx.message.id:
            await safe_send(ctx.channel, "❌ Aucun message valide à réagir.", delete_after=5)
            return

        try:
            # Ajoute la réaction
            await target_message.add_reaction(emoji)
            print(f"✅ Réaction {emoji} ajoutée à {target_message.id}")

            await asyncio.sleep(180)  # Attente 3 min

            # Retire la réaction du bot
            await target_message.remove_reaction(emoji, ctx.guild.me)
            print(f"🔁 Réaction {emoji} retirée de {target_message.id}")
        except Exception as e:
            print(f"⚠️ Erreur lors de la réaction : {e}")

    def cog_load(self):
        if hasattr(self, "react"):
            self.react.category = "Général"

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReactCommand(bot)
    await bot.add_cog(cog)


