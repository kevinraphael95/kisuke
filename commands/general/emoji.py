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
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _display_emojis(self, channel: discord.abc.Messageable, guild: discord.Guild, emoji_names: tuple[str]):
        try:
            if emoji_names:
                found = []
                not_found = []
                for raw_name in emoji_names:
                    name = raw_name.lower().strip(":")
                    match = next((e for e in guild.emojis if e.name.lower() == name), None)
                    if match:
                        found.append(str(match))
                    else:
                        not_found.append(raw_name)
                if found:
                    await safe_send(channel, " ".join(found))
                if not_found:
                    await safe_send(channel, "❌ Emoji(s) introuvable(s) : " + ", ".join(f"`{name}`" for name in not_found))
            else:
                animated_emojis = [str(e) for e in guild.emojis if e.animated]
                if not animated_emojis:
                    await safe_send(channel, "❌ Ce serveur n'a aucun emoji animé.")
                    return
                description = ""
                for emoji in animated_emojis:
                    if len(description) + len(emoji) + 1 > 4096:
                        embed = discord.Embed(
                            title="🎞️ Emojis animés du serveur",
                            description=description,
                            color=discord.Color.purple()
                        )
                        await safe_send(channel, embed=embed)
                        description = ""
                    description += emoji + " "
                if description:
                    embed = discord.Embed(
                        title="🎞️ Emojis animés du serveur",
                        description=description,
                        color=discord.Color.purple()
                    )
                    await safe_send(channel, embed=embed)
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
            pass  # Ignore si la suppression échoue
        await self._display_emojis(ctx.channel, ctx.guild, emoji_names)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH /emoji
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="emoji", description="Affiche un ou plusieurs emojis du serveur.")
    @app_commands.describe(
        emojis="Noms des emojis à afficher, séparés par des espaces (optionnel)"
    )
    async def slash_emoji(self, interaction: discord.Interaction, *, emojis: str = ""):
        """Commande slash qui affiche des emojis du serveur."""
        await interaction.response.defer()
        emoji_names = tuple(emojis.split()) if emojis else ()
        await self._display_emojis(interaction.channel, interaction.guild, emoji_names)
        try:
            await interaction.delete_original_response()
        except Exception:
            pass


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = EmojiCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)



