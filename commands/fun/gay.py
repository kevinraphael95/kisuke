import discord
from discord.ext import commands
import hashlib
import random

class GayCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gay", help="✨ Révèle ton niveau de flamboyance avec panache.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def gay(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id).encode()

        # Compatibilité stable par utilisateur
        hash_val = hashlib.md5(user_id).digest()
        pourcentage = int.from_bytes(hash_val, 'big') % 101

        # Réactions excentriques selon le palier
        paliers = [
            (90, 101, "🌈✨ Ultra Fabulous ✨🌈", [
                "Tu rayonnes plus fort que le Bankai d’un capitaine 🪩",
                "Ton aura gay est détectable depuis la Soul Society !",
                "Lady Gaga t’appelle ‘sempai’ 💃"
            ], 0xff69b4),
            (70, 89, "💖 Très Audacieux.se 💖", [
                "Un mélange de charme et de chaos 😘",
                "T’as probablement un éventail sur toi en ce moment.",
                "T’as vu *Yoruichi* et dit : oui. Juste oui."
            ], 0xff77ff),
            (50, 69, "😏 Fluidité maîtrisée 😏", [
                "Tu vis dans l’ambiguïté artistique 🎨",
                "Tu préfères les zanpakutō à double tranchant...",
                "Tu dis 'no homo', mais ton reiatsu dit 'full homo'."
            ], 0xaa66ff),
            (30, 49, "🤨 En questionnement existentiel 🤨", [
                "Tu t’es demandé une fois si *Renji* portait vraiment un pantalon.",
                "Tu regardes les scènes de combat... pour le *subtext*.",
                "Tu marches droit mais penches un peu, t’sais."
            ], 0x8888ff),
            (0, 29, "🧍‍♂️ Très... très hétéro 🧍‍♂️", [
                "Tu confonds *Drag Race* avec *Course de rue* 🏎️",
                "Ton style c’est ‘camouflage émotionnel’.",
                "Tu t’égares ici... mais on t’accueille quand même 😌"
            ], 0x5555ff),
        ]

        for min_val, max_val, titre, messages, color in paliers:
            if min_val <= pourcentage <= max_val:
                desc = random.choice(messages)
                embed = discord.Embed(
                    title=f"🎭 {titre}",
                    description=f"**{member.display_name}** est gay à **{pourcentage}%**",
                    color=color
                )
                embed.add_field(name="💬 Diagnostic Reiatsu", value=desc, inline=False)
                embed.set_footer(text="Test certifié par Mayuri et sa fashion team 👘")
                await ctx.send(embed=embed)
                return

# Chargement automatique
async def setup(bot):
    cog = GayCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
