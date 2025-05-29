# ────────────────────────────────────────────────────────────────
#        😄 COMMANDE DISCORD - EMOJIS DU SERVEUR        
# ────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands

# ────────────────────────────────────────────────────────────────═
# 📦 Classe principale de la commande "emoji"
# ────────────────────────────────────────────────────────────────═
class EmojiCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ───────────────────────────────────────────────
    # 😎 Commande !emoji ou !e : affiche des emojis
    # Cooldown : 1 fois toutes les 3 secondes par utilisateur
    # ───────────────────────────────────────────────
    @commands.command(
        name="emoji",
        aliases=["e"],
        help="😄 Affiche un ou plusieurs emojis du serveur."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def emoji(self, ctx, *emoji_names):
        # 🧹 Tentative de suppression du message de commande
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass  # ❌ Ignore les erreurs si non autorisé

        # 🔎 Si des noms d'emojis sont fournis
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

            # ✅ Affiche les emojis trouvés
            if found:
                await ctx.send(" ".join(found))

            # ❌ Affiche les noms non trouvés
            if not_found:
                await ctx.send("❌ Emoji(s) introuvable(s) : " + ", ".join(f"`{name}`" for name in not_found))

        # 📋 Si aucun nom fourni, affiche tous les emojis animés
        else:
            animated_emojis = [str(e) for e in ctx.guild.emojis if e.animated]
            if not animated_emojis:
                await ctx.send("❌ Ce serveur n'a aucun emoji animé.")
                return

            # 🧾 Envoi par lots (Discord limite les embeds à 4096 caractères)
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

            # 📨 Envoi du dernier lot
            if description:
                await ctx.send(embed=discord.Embed(
                    title="🎞️ Emojis animés du serveur",
                    description=description,
                    color=discord.Color.purple()
                ))

# ────────────────────────────────────────────────────────────────═
# 🔌 Fonction de setup pour charger le Cog
# ────────────────────────────────────────────────────────────────═
async def setup(bot):
    cog = EmojiCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"  # 📁 Classement dans la catégorie "Fun"
    await bot.add_cog(cog)
