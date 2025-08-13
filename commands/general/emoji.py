# ────────────────────────────────────────────────────────────────────────────────
# 📌 emoji_command.py — Commande interactive !emoji / !e et /emoji
# Objectif : Afficher un ou plusieurs emojis du serveur via une commande
# Catégorie : 🎉 Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send  # ✅ Utilisation sécurisée

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class EmojiCommand(commands.Cog):
    """
    Commande !emoji / !e et /emoji — Affiche un ou plusieurs emojis du serveur.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🛠️ Fonctions internes utilitaires
    # ────────────────────────────────────────────────────────────────────────────
    def _find_emojis(self, emoji_names: tuple[str], guild: discord.Guild):
        """Retourne deux listes : (trouvés, introuvables)"""
        found, not_found = [], []
        for raw_name in emoji_names:
            name = raw_name.lower().strip(":")
            match = discord.utils.find(lambda e: e.name.lower() == name and e.available, guild.emojis)
            if match:
                found.append(str(match))
            else:
                not_found.append(raw_name)
        return found, not_found

    async def _send_text_paginated(self, channel, emojis: list[str]):
        """Envoie les emojis sous forme de texte brut, en plusieurs messages si nécessaire."""
        message = ""
        for emoji in emojis:
            if len(message) + len(emoji) + 1 > 2000:
                await safe_send(channel, message.strip())
                message = ""
            message += emoji + " "
        if message:
            await safe_send(channel, message.strip())

    async def _display_emojis(self, channel, guild, emoji_names: tuple[str]):
        """Affiche les emojis demandés ou tous les animés si aucun argument."""
        try:
            if emoji_names:
                found, not_found = self._find_emojis(emoji_names, guild)

                if found:
                    await safe_send(channel, " ".join(found))

                if not_found:
                    await safe_send(channel, f"❌ Emojis introuvables : {', '.join(f'`{n}`' for n in not_found)}")
            else:
                animated_emojis = [str(e) for e in guild.emojis if e.animated and e.available]
                if not animated_emojis:
                    await safe_send(channel, "❌ Ce serveur n'a aucun emoji animé.")
                    return
                await self._send_text_paginated(channel, animated_emojis)

        except Exception as e:
            print(f"[ERREUR affichage emojis] {e}")
            await safe_send(channel, "❌ Une erreur est survenue lors de l'affichage des emojis.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX !emoji / !e
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="emoji",
        aliases=["e"],
        help="😄 Affiche un ou plusieurs emojis du serveur.",
        description="Affiche les emojis demandés ou tous les emojis animés du serveur si aucun argument."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def prefix_emoji(self, ctx: commands.Context, *emoji_names):
        """Affiche les emojis du serveur en fonction des arguments fournis."""
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass
        await self._display_emojis(ctx.channel, ctx.guild, emoji_names)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH /emoji avec auto-complétion
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="emoji", description="Affiche un ou plusieurs emojis du serveur.")
    @app_commands.describe(emojis="Noms des emojis à afficher, séparés par des espaces (optionnel)")
    async def slash_emoji(self, interaction: discord.Interaction, *, emojis: str = ""):
        """Commande slash qui affiche des emojis du serveur."""
        await interaction.response.defer()
        emoji_names = tuple(emojis.split()) if emojis else ()
        await self._display_emojis(interaction.channel, interaction.guild, emoji_names)
        try:
            await interaction.delete_original_response()
        except Exception:
            pass

    @slash_emoji.autocomplete("emojis")
    async def autocomplete_emojis(self, interaction: discord.Interaction, current: str):
        """Auto-complétion qui propose les noms d'emojis du serveur."""
        suggestions = [e.name for e in interaction.guild.emojis if e.available]
        return [
            app_commands.Choice(name=s, value=s)
            for s in suggestions if current.lower() in s.lower()
        ][:25]  # Discord limite à 25 choix

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = EmojiCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
