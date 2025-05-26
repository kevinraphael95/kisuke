import discord
from discord.ext import commands
import hashlib

class GayCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gay", help="Découvre à quel point toi ou quelqu’un d’autre est gay (résultat fixe et amusant).")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # ⏱️ Cooldown 3s
    async def gay(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id).encode()

        # Hash déterministe
        hash_val = hashlib.md5(user_id).digest()
        pourcentage = int.from_bytes(hash_val, 'big') % 101

        if pourcentage >= 90:
            niveau = "🌈 Tu es un arc-en-ciel vivant !"
        elif pourcentage >= 70:
            niveau = "💅 Clairement dans la vibe."
        elif pourcentage >= 50:
            niveau = "😉 Des tendances, peut-être ?"
        elif pourcentage >= 30:
            niveau = "🤨 C'est pas totalement hétéro là..."
        else:
            niveau = "🧍‍♂️ Un peu trop hétéro, ça..."

        await ctx.send(f"🏳️‍🌈 {member.display_name} est gay à **{pourcentage}%** !\n{niveau}")

# Chargement auto
async def setup(bot):
    cog = GayCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
