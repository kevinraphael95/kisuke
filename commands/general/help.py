# ──────────────────────────────────────────────────────────────
# 📁 FICHIER : commands/general/help.py
# ──────────────────────────────────────────────────────────────
# 🧾 COMMANDE : !help
# 📚 FONCTION : Affiche toutes les commandes ou les infos détaillées
# 📂 CATÉGORIE : Général (définie dynamiquement)
# 🕒 COOLDOWN : 5 secondes par utilisateur
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from bot import get_prefix  # 🔧 Fonction utilitaire pour le préfixe

# ──────────────────────────────────────────────────────────────
# 🧠 CLASSE PRINCIPALE : HelpCommand
# ──────────────────────────────────────────────────────────────
class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # 🔌 Connexion au bot principal

    # ──────────────────────────────────────────────────────────
    # 💬 COMMANDE : !help [commande]
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="help",
        help="Affiche la liste des commandes ou les infos sur une commande spécifique."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)  # 🕒 Anti-spam 5s
    async def help_func(self, ctx: commands.Context, commande: str = None):
        prefix = get_prefix(self.bot, ctx.message)

        # ──────────────
        # 📜 LISTE GLOBALE
        # ──────────────
        if commande is None:
            categories = {}  # 🧺 Dictionnaire vide pour regrouper par catégorie

            for cmd in self.bot.commands:
                if cmd.hidden:
                    continue  # 🚫 Ne pas afficher les commandes cachées

                cat = getattr(cmd, "category", "Autres")  # 🏷️ Récupère la catégorie ou "Autres"
                categories.setdefault(cat, []).append(cmd)  # 📌 Ajoute à la bonne catégorie

            # 🎨 Construction de l'embed global
            embed = discord.Embed(
                title="📜 Liste des commandes par catégorie",
                color=discord.Color.blue()
            )

            for cat, cmds in sorted(categories.items()):
                cmds.sort(key=lambda c: c.name)  # 🔠 Trie alphabétique
                description = "\n".join(
                    f"`{prefix}{c.name}` : {c.help or 'Pas de description.'}" for c in cmds
                )
                embed.add_field(name=f"📂 {cat}", value=description, inline=False)

            embed.set_footer(text=f"Utilise {prefix}help <commande> pour plus de détails.")
            await ctx.send(embed=embed)

        # ──────────────
        # 🔍 AIDE SPÉCIFIQUE
        # ──────────────
        else:
            cmd = self.bot.get_command(commande)

            if cmd is None:
                await ctx.send(f"❌ La commande `{commande}` n'existe pas.")
                return

            embed = discord.Embed(
                title=f"ℹ️ Aide pour `{prefix}{cmd.name}`",
                color=discord.Color.green()
            )
            embed.add_field(name="📄 Description", value=cmd.help or "Pas de description.", inline=False)

            if cmd.aliases:
                aliases = ", ".join(f"`{a}`" for a in cmd.aliases)
                embed.add_field(name="🔁 Alias", value=aliases, inline=False)

            embed.set_footer(text="📌 Syntaxe : <obligatoire> [optionnel]")
            await ctx.send(embed=embed)

    # ──────────────────────────────────────────────────────────
    # 🏷️ CATÉGORISATION DYNAMIQUE
    # ──────────────────────────────────────────────────────────
    def cog_load(self):
        self.help_func.category = "Général"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HelpCommand(bot)

    # ✅ Sécurité : on attribue la catégorie si elle n'est pas définie
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"

    await bot.add_cog(cog)
    print("✅ Cog chargé : HelpCommand (catégorie = Général)")
