# ────────────────────────────────────────────────────────────────────────────────
# 📌 sfm_command.py — Commande interactive !sfm
# Objectif : Un shifumi inspiré de Bleach (Shinigami, Quincy, Hollow)
# Catégorie : Bleach
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import asyncio
import random
import discord
from discord.ext import commands

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class SfmCommand(commands.Cog):
    """
    Commande !sfm — Shifumi mais version Bleach avec Shinigami, Quincy et Hollow.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="sfm",
        help="⚔️ Shifumi mais avec Shinigami, Quincy et Hollow !",
        description="Duel entre deux joueurs (ou contre le bot) basé sur pierre-papier-ciseaux version Bleach."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def sfm(self, ctx: commands.Context, adversaire: discord.Member = None):
        joueur1 = ctx.author
        joueur2 = adversaire or self.bot.user

        emojis = {
            "shinigami": "🗡️",
            "quincy": "🎯",
            "hollow": "💀"
        }
        forces = {
            "shinigami": "hollow",  # Shinigami bat Hollow
            "hollow": "quincy",     # Hollow bat Quincy
            "quincy": "shinigami"   # Quincy bat Shinigami
        }

        # Embed d'intro avec règles
        embed_intro = discord.Embed(
            title="Shifumi mais version Bleach",
            description=(
                "🗡️ Shinigami bat 🎯 Quincy\n"
                "🎯 Quincy bat 💀 Hollow\n"
                "💀 Hollow bat 🗡️ Shinigami\n\n"
                "Réagissez avec l’emoji correspondant à votre choix."
            ),
            color=discord.Color.purple()
        )
        embed_intro.set_footer(text="Vous avez 30 secondes pour choisir.")

        # Étape 1 : Choix joueur 1
        message = await ctx.send(content=f"**{joueur1.mention}**, choisis ton camp :", embed=embed_intro)
        for emoji in emojis.values():
            await message.add_reaction(emoji)

        def check_reaction_j1(reaction, user):
            return (
                user == joueur1
                and str(reaction.emoji) in emojis.values()
                and reaction.message.id == message.id
            )

        try:
            reaction_j1, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check_reaction_j1)
        except asyncio.TimeoutError:
            return await ctx.send("⏰ Temps écoulé. Partie annulée.")

        choix_j1 = next(race for race, emj in emojis.items() if emj == str(reaction_j1.emoji))

        # Étape 2 : Choix joueur 2 (humain ou bot)
        if joueur2 == self.bot.user:
            choix_j2 = random.choice(list(emojis.keys()))
        else:
            embed_j2 = discord.Embed(
                title="À ton tour !",
                description=f"**{joueur2.mention}**, choisis ton camp : 🗡️ Shinigami, 🎯 Quincy ou 💀 Hollow",
                color=discord.Color.orange()
            )
            message2 = await ctx.send(embed=embed_j2)
            for emoji in emojis.values():
                await message2.add_reaction(emoji)

            def check_reaction_j2(reaction, user):
                return (
                    user == joueur2
                    and str(reaction.emoji) in emojis.values()
                    and reaction.message.id == message2.id
                )

            try:
                reaction_j2, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check_reaction_j2)
            except asyncio.TimeoutError:
                return await ctx.send("⏰ Temps écoulé pour le second joueur. Partie annulée.")

            choix_j2 = next(race for race, emj in emojis.items() if emj == str(reaction_j2.emoji))

        # Résultat
        if choix_j1 == choix_j2:
            resultat = "⚖️ Égalité parfaite entre deux âmes puissantes !"
            couleur = discord.Color.gold()
        elif forces[choix_j1] == choix_j2:
            resultat = f"🏆 **{joueur1.display_name}** l’emporte ! {emojis[choix_j1]} bat {emojis[choix_j2]}"
            couleur = discord.Color.green()
        else:
            resultat = f"🏆 **{joueur2.display_name}** l’emporte ! {emojis[choix_j2]} bat {emojis[choix_j1]}"
            couleur = discord.Color.red()

        embed_result = discord.Embed(
            title="🔹 Combat spirituel terminé ! 🔹",
            color=couleur
        )
        embed_result.add_field(name=joueur1.display_name, value=f"{emojis[choix_j1]} `{choix_j1.capitalize()}`", inline=True)
        embed_result.add_field(name=joueur2.display_name, value=f"{emojis[choix_j2]} `{choix_j2.capitalize()}`", inline=True)
        embed_result.add_field(name="Résultat", value=resultat, inline=False)

        await ctx.send(embed=embed_result)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SfmCommand(bot)
    for command in cog.get_commands():
        command.category = "Bleach"
    await bot.add_cog(cog)
