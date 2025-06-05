# ────────────────────────────────────────────────────────────────
# 🤔 TU PRÉFÈRES QUI ? - COMMANDE DE VOTE FUN & IMMERSIVE
# ────────────────────────────────────────────────────────────────
# 🏆 TOP PERSOS - CLASSEMENT DES PERSONNAGES PRÉFÉRÉS
# ────────────────────────────────────────────────────────────────
# 🔄 COMMANDE ADMIN - RESET VOTES PERSOS (SUPABASE)
# ────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
import json
import random
from supabase_client import supabase  # Assure-toi que ce client est bien configuré

# ────────────────────────────────────────────────────────────────
# TuPrefCommand
class TuPrefCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="tupref",
        aliases=["tp"],
        help="🤔 Choisis ton personnage préféré entre deux propositions aléatoires."
    )
    @commands.cooldown(rate=1, per=3600, type=commands.BucketType.user)
    async def tupref(self, ctx):
        try:
            with open("data/bleach_personnages.json", "r", encoding="utf-8") as f:
                persos = json.load(f)

            if len(persos) < 2:
                await ctx.send("❌ Il faut au moins deux personnages pour lancer un vote.")
                return

            p1, p2 = random.sample(persos, 2)
            nom1, nom2 = p1["nom"], p2["nom"]

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

# ────────────────────────────────────────────────────────────────
# TopPersoCommand
class TopPersoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="tupreftop",
        aliases=["tpt"],
        aliases=["toptupref"],
        help="📊 Affiche les personnages les plus aimés par les votes de la communauté."
    )
    async def topperso(self, ctx, limit: int = 10):
        if limit < 1 or limit > 50:
            await ctx.send("❌ Le nombre doit être **entre 1 et 50** pour éviter de surcharger le classement.")
            return

        try:
            result = supabase.table("perso_votes") \
                             .select("nom", "votes") \
                             .order("votes", desc=True) \
                             .limit(limit) \
                             .execute()
        except Exception as e:
            await ctx.send(f"⚠️ Erreur lors de la récupération des données : `{e}`")
            return

        if not result.data:
            await ctx.send("📉 Aucun vote n’a encore été enregistré. Sois le premier à voter !")
            return

        embed = discord.Embed(
            title=f"🏆 Top {limit} des personnages les plus aimés",
            description="Voici le classement des **plus grands favoris** de la Soul Society 🌌",
            color=discord.Color.gold()
        )
        embed.set_footer(text="🔥 Basé sur les votes enregistrés par la communauté")

        medals = ["🥇", "🥈", "🥉"] + ["🔹"] * (limit - 3)
        for i, row in enumerate(result.data, start=1):
            emoji = medals[i - 1] if i <= len(medals) else "🔹"
            embed.add_field(
                name=f"{emoji} {i}. {row['nom']}",
                value=f"💖 **{row['votes']}** votes",
                inline=False
            )

        await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────
# ResetPersoCommand
class ResetPersoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="tuprefreset",
        aliases=["tpr"],
        help="(Admin) Réinitialise tous les votes des personnages."
    )
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def resetperso(self, ctx):
        try:
            result = supabase.table("perso_votes").delete().neq("nom", "").execute()
            if result.get("error"):
                raise Exception(result["error"]["message"])
            await ctx.send("🗑️ Tous les votes ont été réinitialisés avec succès.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue lors de la réinitialisation :\n```{e}```")

# ────────────────────────────────────────────────────────────────
# Chargement automatique des 3 cogs
async def setup(bot):
    cogs = [TuPrefCommand(bot), TopPersoCommand(bot), ResetPersoCommand(bot)]
    for cog in cogs:
        for command in cog.get_commands():
            command.category = "Bleach"
        await bot.add_cog(cog)
