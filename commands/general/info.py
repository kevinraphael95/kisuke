# ──────────────────────────────────────────────────────────────
# 📁 FICHIER : commands/general/info.py
# ──────────────────────────────────────────────────────────────
# 🧾 COMMANDE : !info
# 📚 FONCTION : Affiche un résumé des nouveautés et de l’état du bot
# 📂 CATÉGORIE : Général
# 🕒 COOLDOWN : 3 secondes par utilisateur
# ──────────────────────────────────────────────────────────────

import discord
from discord.ext import commands

# ──────────────────────────────────────────────────────────────
# 🔧 COG : InfoCommand
# ──────────────────────────────────────────────────────────────
class InfoCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # 🔌 Référence au bot principal

    # ──────────────────────────────────────────────────────────
    # 💬 COMMANDE : !info
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="info",
        help="Affiche des informations sur l'état du bot."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 Anti-spam : 3s
    async def info(self, ctx: commands.Context):
        # 🎨 Création de l'embed
        embed = discord.Embed(
            title="📊 État du bot",
            description="Voici quelques informations sur l'état actuel du bot.",
            color=discord.Color.gold()
        )

        # 🧱 Ajout des sections d'information
        embed.add_field(
            name="🔧 Réorganisation",
            value="Le **code du bot** a été complètement **réorganisé**.\n"
                  "Les commandes ne sont plus regroupées dans `bot.py`.",
            inline=False
        )

        embed.add_field(
            name="📘 Commande help",
            value="La **commande help** sera réparée quand elle sera réparée.",
            inline=False
        )

        embed.add_field(
            name="💠 Reiatsu",
            value="Le spawn auto de reiatsu est **de retour**… normalement 👀",
            inline=False
        )

        embed.add_field(
            name="🧘 Nouvelles commandes",
            value="`tupref` et `topperso` sont maintenant disponibles.",
            inline=False
        )

        embed.add_field(
            name="🕹️ RPG",
            value="Une nouvelle commande RPG a été ajoutée... mystérieusement.",
            inline=False
        )

        embed.set_footer(text="📅 Dernière mise à jour : Mai 2025")
        await ctx.send(embed=embed)

    # ──────────────────────────────────────────────────────────
    # 🏷️ CATEGORISATION AUTOMATIQUE
    # ──────────────────────────────────────────────────────────
    def cog_load(self):
        self.info.category = "Général"  # ✅ Pour l’organisation de !help/!commandes

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGER LE COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(InfoCommand(bot))
    print("✅ Cog chargé : InfoCommand (catégorie = Général)")
