import discord
import json
from discord.ext import commands

class PersoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="perso", help="Découvre quel personnage de Bleach tu es (toujours le même pour toi).")
    async def perso(self, ctx):
        try:
            with open("data/bleach_characters.json", "r", encoding="utf-8") as f:
                characters = json.load(f)

            if not characters or not isinstance(characters, list):
                await ctx.send("❌ Le fichier des personnages est vide ou invalide.")
                return

            user_id = ctx.author.id
            index = (user_id * 31 + 17) % len(characters)
            personnage = characters[index]
            await ctx.send(f"{ctx.author.mention}, tu es **{personnage}** ! (C'est ta destinée dans le monde de Bleach 🔥)")

        except FileNotFoundError:
            await ctx.send("❌ Fichier `bleach_characters.json` introuvable.")
        except json.JSONDecodeError:
            await ctx.send("❌ Le fichier JSON est mal formaté.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur : {e}")

# Chargement du module
async def setup(bot):
    cog = PersoCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
