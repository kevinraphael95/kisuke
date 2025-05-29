# ──────────────────────────────────────────────────────────────
# 📁 FICHIER : commands/general/commandes.py
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ext.commands import Context
from bot import get_prefix  # Fonction pour récupérer dynamiquement le préfixe

# ──────────────────────────────────────────────────────────────
# 🧠 CLASSE DU COG : contient la logique de la commande
# ──────────────────────────────────────────────────────────────
class CommandesCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """
        Initialise le cog avec une référence au bot principal.
        """
        self.bot = bot

    # ──────────────────────────────────────────────────────────
    # 💬 COMMANDE !commandes
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="commandes",
        help="Affiche toutes les commandes disponibles, classées par catégorie."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def commandes(self, ctx: Context):
        """
        Envoie un ou plusieurs embeds listant toutes les commandes du bot,
        triées par catégorie. Navigation par réactions.
        """
        # 🔍 Récupérer le préfixe dynamique
        prefix = get_prefix(self.bot, ctx.message)

        # ──────────────────────────────────────────────────────
        # 📚 REGROUPEMENT DES COMMANDES PAR CATÉGORIE
        # ──────────────────────────────────────────────────────
        categories = {}  # Dictionnaire : {catégorie: [commandes]}
        for cmd in self.bot.commands:
            if cmd.hidden:
                continue  # 🚫 On ignore les commandes cachées (hidden=True)
            cat = getattr(cmd, "category", "Autres")  # 🏷️ On récupère la catégorie (ou "Autres" par défaut)
            categories.setdefault(cat, []).append(cmd)

        # ──────────────────────────────────────────────────────
        # 🖼️ CRÉATION DES EMBEDS PAR CATÉGORIE
        # ──────────────────────────────────────────────────────
        embeds = []
        for cat, cmds in sorted(categories.items()):
            cmds.sort(key=lambda c: c.name)  # 🔤 Tri alphabétique des commandes
            description = "\n".join(
                f"`{prefix}{cmd.name}` : {cmd.help or 'Pas de description.'}"
                for cmd in cmds
            )

            embed = discord.Embed(
                title=f"📂 Catégorie : {cat}",
                description=description,
                color=discord.Color.blurple()
            )
            embed.set_footer(text="Utilise !help <commande> pour plus d'infos.")
            embeds.append(embed)

        # ──────────────────────────────────────────────────────
        # 📤 ENVOI DU PREMIER EMBED
        # ──────────────────────────────────────────────────────
        message = await ctx.send(embed=embeds[0])

        # 🎯 Si une seule page, pas besoin de réactions
        if len(embeds) <= 1:
            return

        # ──────────────────────────────────────────────────────
        # ➕ AJOUT DES RÉACTIONS POUR NAVIGATION
        # ──────────────────────────────────────────────────────
        await message.add_reaction("⬅️")
        await message.add_reaction("➡️")
        current_page = 0  # 🔢 Index de la page affichée

        def check(reaction, user):
            """
            Fonction de vérification : seule la personne ayant lancé
            la commande peut interagir avec les boutons.
            """
            return (
                user == ctx.author and
                str(reaction.emoji) in ["⬅️", "➡️"] and
                reaction.message.id == message.id
            )

        # ──────────────────────────────────────────────────────
        # 🔁 BOUCLE DE PAGINATION (attente de réactions)
        # ──────────────────────────────────────────────────────
        while True:
            try:
                # ⏳ On attend que l'utilisateur clique sur une réaction
                reaction, user = await self.bot.wait_for(
                    "reaction_add", timeout=60.0, check=check
                )

                # 🔁 Gestion des pages
                if str(reaction.emoji) == "➡️":
                    current_page = (current_page + 1) % len(embeds)
                elif str(reaction.emoji) == "⬅️":
                    current_page = (current_page - 1) % len(embeds)

                # ✏️ Mise à jour de l'embed
                await message.edit(embed=embeds[current_page])
                await message.remove_reaction(reaction, user)

            except Exception:
                break  # 🧨 Timeout ou erreur → on sort de la boucle

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP : Fonction appelée automatiquement par le bot
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    """
    Cette fonction est appelée par le bot au démarrage pour charger ce cog.
    On y ajoute la classe de commande, puis on attribue la catégorie.
    """
    cog = CommandesCommand(bot)
    await bot.add_cog(cog)

    # 📌 Attribution manuelle de la catégorie pour affichage personnalisé
    if hasattr(cog, "commandes"):
        cog.commandes.category = "Général"

    print("✅ Cog chargé : CommandesCommand (catégorie = Général)")
