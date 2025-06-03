# ────────────────────────────────────────────────────────────────────────────────
# 📌 emoji_command.py — Commande interactive !emoji / !e
# Objectif : Afficher un ou plusieurs emojis du serveur via une commande
# Catégorie : 🎉 Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class EmojiCommand(commands.Cog):
    """
    Commande !emoji / !e — Affiche un ou plusieurs emojis du serveur.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="emoji",
        aliases=["e"],
        help="😄 Affiche un ou plusieurs emojis du serveur.",
        description="Affiche les emojis demandés ou tous les emojis animés du serveur si aucun argument."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def emoji(self, ctx: commands.Context, *emoji_names):
        """Affiche les emojis du serveur en fonction des arguments fournis."""
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass  # Ignore si pas d'autorisation

        if emoji_names:
            found = []
            not_found = []

            for raw_name in emoji_names:
                name = raw_name.strip(":").lower()
                match = next((e for e in ctx.guild.emojis if e.name.lower() == name), None)
                if match:
                    found.append(str(match))
                else:
                    not_found.append(raw_name)

            if found:
                await ctx.send(" ".join(found))

            if not_found:
                await ctx.send("❌ Emoji(s) introuvable(s) : " + ", ".join(f"`{name}`" for name in not_found))

        else:
            animated_emojis = [str(e) for e in ctx.guild.emojis if e.animated]
            if not animated_emojis:
                await ctx.send("❌ Ce serveur n'a aucun emoji animé.")
                return

            description = ""
            for emoji in animated_emojis:
                if len(description) + len(emoji) + 1 > 4096:
                    embed = discord.Embed(
                        title="🎞️ Emojis animés du serveur",
                        description=description,
                        color=discord.Color.purple()
                    )
                    await ctx.send(embed=embed)
                    description = ""
                description += emoji + " "

            if description:
                embed = discord.Embed(
                    title="🎞️ Emojis animés du serveur",
                    description=description,
                    color=discord.Color.purple()
                )
                await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = EmojiCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
