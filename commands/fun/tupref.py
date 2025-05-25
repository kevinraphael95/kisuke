import discord
from discord.ext import commands
import json
import random
from supabase_client import supabase

class TuPrefCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tupref", help="Choisis ton personnage préféré entre deux options.")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def tupref(self, ctx):
        try:
            with open("data/bleach_personnages.json", "r", encoding="utf-8") as f:
                persos = json.load(f)

            p1, p2 = random.sample(persos, 2)

            embed = discord.Embed(
                title="Tu préfères qui ? 🤔",
                description=f"⚔️ {p1} **ou** 🛡️ {p2}",
                color=discord.Color.orange()
            )
            message = await ctx.send(embed=embed)
            await message.add_reaction("⚔️")
            await message.add_reaction("🛡️")

            def check(reaction, user):
                return (
                    user == ctx.author
                    and str(reaction.emoji) in ["⚔️", "🛡️"]
                    and reaction.message.id == message.id
                )

            try:
                reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            except:
                await ctx.send("⏰ Temps écoulé.")
                return

            selected = p1 if str(reaction.emoji) == "⚔️" else p2

            # Vérifie si le perso existe déjà dans la DB
            data = supabase.table("perso_votes").select("*").eq("nom", selected).execute()
            if data.data:
                votes = data.data[0]["votes"] + 1
                supabase.table("perso_votes").update({"votes": votes}).eq("nom", selected).execute()
            else:
                supabase.table("perso_votes").insert({"nom": selected, "votes": 1}).execute()

            await ctx.send(f"✅ {ctx.author.mention} a voté pour **{selected}** !")

        except Exception as e:
            await ctx.send(f"⚠️ Erreur : {e}")

# Chargement auto
async def setup(bot):
    cog = TuPrefCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
