import discord
from discord.ext import commands

class EmojiCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="emoji", aliases=["e"], help="Affiche un ou plusieurs emojis du serveur.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown utilisateur 3s
    async def emoji(self, ctx, *emoji_names):
        try:
            await ctx.message.delete()  # Supprime la commande
        except (discord.Forbidden, discord.HTTPException):
            pass  # Ignore les erreurs de suppression

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
                    await ctx.send(embed=discord.Embed(
                        title="🎞️ Emojis animés du serveur",
                        description=description,
                        color=discord.Color.purple()
                    ))
                    description = ""
                description += emoji + " "

            if description:
                await ctx.send(embed=discord.Embed(
                    title="🎞️ Emojis animés du serveur",
                    description=description,
                    color=discord.Color.purple()
                ))

# Chargement automatique + définition de catégorie
async def setup(bot):
    cog = EmojiCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
