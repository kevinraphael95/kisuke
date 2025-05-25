import discord
import json
import random
from discord.ext import commands

class HollowifyCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hollowify", help="Transforme un utilisateur en Hollow avec une description stylée.")
    async def hollowify(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        try:
            with open("data/hollow_data.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            prefixes = data.get("prefixes", [])
            suffixes = data.get("suffixes", [])
            descriptions = data.get("descriptions", [])

            if not prefixes or not suffixes or not descriptions:
                await ctx.send("❌ Le fichier `hollow_data.json` est incomplet ou mal formaté.")
                return

            nom_hollow = random.choice(prefixes) + random.choice(suffixes)
            description = random.choice(descriptions)

            await ctx.send(
                f"💀 **{member.display_name}** se transforme en Hollow : **{nom_hollow}** !\n{description}"
            )

        except FileNotFoundError:
            await ctx.send("❌ Le fichier `hollow_data.json` est introuvable.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {e}")

# Chargement du cog et ajout de la catégorie
async def setup(bot):
    cog = HollowifyCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
