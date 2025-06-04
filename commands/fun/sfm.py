# ────────────────────────────────────────────────────────────────
# ⚔️ SFM - SHINIGAMI vs QUINCY vs HOLLOW
# ────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import asyncio
import random
import discord
from discord.ext import commands

# ────────────────────────────────────────────────────────────────
# 🧩 COMBAT RP : INSPIRÉ DE BLEACH
# ────────────────────────────────────────────────────────────────
class SfmCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────
    # 🗡️ COMMANDE : !sfm [@adversaire]
    # Permet un duel entre deux joueurs (ou contre le bot)
    # Basé sur un système de forces comme pierre-papier-ciseaux
    # ──────────────────────────────────────────────────────
    @commands.command(
        name="sfm",
        help="⚔️ Shifumi mais avec Shinigami, Quincy et Hollow !"
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def sfm(self, ctx, adversaire: discord.Member = None):
        joueur1 = ctx.author
        joueur2 = adversaire or self.bot.user

        # 🧬 Définition des races et forces
        emojis = {
            "shinigami": "🗡️",
            "quincy": "🎯",
            "hollow": "💀"
        }

        # Qui bat qui (Shinigami > Hollow > Quincy > Shinigami)
        forces = {
            "shinigami": "hollow",
            "hollow": "quincy",
            "quincy": "shinigami"
        }

        # 🔸 Étape 1 : Choix du joueur 1
        message = await ctx.send(
            f"🗡️ ➡️ 🎯 ➡️ 💀 ➡️ 🗡️\➡n"
            f"**{joueur1.mention}**, choisis :\n"
            f"🗡️ Shinigami — 🎯 Quincy — 💀 Hollow"
        )
        for emoji in emojis.values():
            await message.add_reaction(emoji)

        def check_reaction(reaction, user):
            return (
                user == joueur1 and
                str(reaction.emoji) in emojis.values() and
                reaction.message.id == message.id
            )

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check_reaction)
        except asyncio.TimeoutError:
            return await ctx.send("⏰ Temps écoulé. Partie annulée.")

        choix_j1 = next(race for race, emoji in emojis.items() if emoji == str(reaction.emoji))

        # 🔸 Étape 2 : Choix du joueur 2 (bot ou humain)
        if joueur2 == self.bot.user:
            choix_j2 = random.choice(list(emojis.keys()))
        else:
            await ctx.send(
                f"**{joueur2.mention}**, à ton tour de choisir :\n"
                f"🗡️ Shinigami — 🎯 Quincy — 💀 Hollow"
            )
            message2 = await ctx.send("Réagis avec l’emoji correspondant à ta race.")

            for emoji in emojis.values():
                await message2.add_reaction(emoji)

            def check_reaction_2(reaction, user):
                return (
                    user == joueur2 and
                    str(reaction.emoji) in emojis.values() and
                    reaction.message.id == message2.id
                )

            try:
                reaction2, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check_reaction_2)
            except asyncio.TimeoutError:
                return await ctx.send("⏰ Temps écoulé pour le second joueur. Partie annulée.")

            choix_j2 = next(race for race, emoji in emojis.items() if emoji == str(reaction2.emoji))

        # 🔸 Étape 3 : Résultat du combat
        if choix_j1 == choix_j2:
            result = "⚖️ Égalité parfaite entre deux âmes puissantes !"
        elif forces[choix_j1] == choix_j2:
            result = f"🏆 **{joueur1.display_name}** l’emporte ! {emojis[choix_j1]} bat {emojis[choix_j2]}"
        else:
            result = f"🏆 **{joueur2.display_name}** l’emporte ! {emojis[choix_j2]} bat {emojis[choix_j1]}"

        # 📢 Affichage final
        await ctx.send(
            f"🔹 **Combat spirituel terminé !** 🔹\n\n"
            f"👤 {joueur1.display_name} : {emojis[choix_j1]} `{choix_j1.capitalize()}`\n"
            f"👤 {joueur2.display_name} : {emojis[choix_j2]} `{choix_j2.capitalize()}`\n\n"
            f"{result}"
        )

# ──────────────────────────────────────────────────────
# 🔌 CHARGEMENT AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────
async def setup(bot):
    cog = SfmCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
