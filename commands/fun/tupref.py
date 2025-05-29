# ────────────────────────────────────────────────────────
# 🤔 TU PRÉFÈRES QUI ? - COMMANDE DE VOTE FUN & IMMERSIVE
# ────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import json
import random
from supabase_client import supabase

class TuPrefCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="tupref",
        help="🤔 Choisis ton personnage préféré entre deux propositions aléatoires."
    )
    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    async def tupref(self, ctx):
        try:
            # 📦 Chargement des personnages
            with open("data/bleach_personnages.json", "r", encoding="utf-8") as f:
                persos = json.load(f)

            if len(persos) < 2:
                await ctx.send("❌ Il faut au moins deux personnages pour lancer un vote.")
                return

            # 🎲 Tirage au sort
            p1, p2 = random.sample(persos, 2)
            nom1, nom2 = p1["nom"], p2["nom"]

            # 🎨 Embed stylisé
            embed = discord.Embed(
                title="💥 Duel de popularité !",
                description=(
                    f"**{ctx.author.display_name}**, choisis entre :\n\n"
                    f"⚔️ **{nom1}**\n"
                    f"🛡️ **{nom2}**\n\n"
                    "Réagis avec ton préféré 👇"
                ),
                color=discord.Color.orange()
            )
            embed.set_footer(text="🕒 Tu as 30 secondes pour choisir.")

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
                await ctx.send("⏰ Temps écoulé. Vote annulé.")
                return

            # 🗳️ Enregistrement du vote
            selection = nom1 if str(reaction.emoji) == "⚔️" else nom2
            try:
                data = supabase.table("perso_votes").select("votes").eq("nom", selection).execute()
                if data.data:
                    votes = data.data[0]["votes"] + 1
                    supabase.table("perso_votes").update({"votes": votes}).eq("nom", selection).execute()
                else:
                    supabase.table("perso_votes").insert({"nom": selection, "votes": 1}).execute()

                await ctx.send(f"✅ {ctx.author.mention} a voté pour **{selection}** !")
            except Exception as db_error:
                await ctx.send(f"⚠️ Une erreur est survenue lors de l’enregistrement du vote : `{db_error}`")

        except FileNotFoundError:
            await ctx.send("❌ Fichier `bleach_personnages.json` introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : `{e}`")

# ────────────────────────────────────────────────
# 🔌 Chargement automatique du cog
# ────────────────────────────────────────────────
async def setup(bot):
    cog = TuPrefCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
