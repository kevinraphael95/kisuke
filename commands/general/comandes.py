# ────────────────────────────────────────────────────────────────────────────────
# 📌 commandes.py — Commande simple /commandes et !commandes
# Objectif : Affiche la liste de toutes les commandes et leurs descriptions (Markdown paginé)
# Catégorie : Utilitaire
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_respond  

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Commandes(commands.Cog):
    """
    Commande /commandes et !commandes — Affiche la liste des commandes et descriptions en Markdown paginé
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne pour créer les pages Markdown
    # ────────────────────────────────────────────────────────────────────────────
    def build_markdown_pages(self, max_chars=1000):
        """Renvoie une liste de blocs Markdown prêts à copier-coller dans un README.md, triés par ordre alphabétique"""
        pages = []
        current_page = ""
        categories = {}

        # Regrouper les commandes par catégorie
        for cmd in self.bot.commands:
            cat = getattr(cmd, "category", "Autre")
            if cat not in categories:
                categories[cat] = []
            desc = cmd.help if cmd.help else "Pas de description."
            categories[cat].append((cmd.name, desc))

        # Parcourir chaque catégorie
        for cat, cmds in categories.items():
            # Trier les commandes par nom
            sorted_cmds = sorted(cmds, key=lambda x: x[0].lower())

            cat_text = f"### 📂 {cat}\n"
            for name, desc in sorted_cmds:
                cmd_text = f"**{name}** : {desc}\n"
                # Vérifier si le bloc dépasse la limite
                if len(current_page) + len(cat_text) + len(cmd_text) > max_chars:
                    pages.append(current_page.strip())
                    current_page = cat_text + cmd_text
                    cat_text = ""  # ne pas répéter le titre de catégorie sur la nouvelle page
                else:
                    current_page += cat_text + cmd_text
                    cat_text = ""
            current_page += "\n"  # saut de ligne entre catégories

        if current_page:
            pages.append(current_page.strip())
        return pages


    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="commandes",
        description="Affiche toutes les commandes disponibles avec leurs descriptions en Markdown (paginé)."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_commandes(self, interaction: discord.Interaction):
        try:
            pages = self.build_markdown_pages()
            response_text = "\n\n---\n\n".join(f"```md\n{p}\n```" for p in pages)
            await safe_respond(interaction, response_text)
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /commandes] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="commandes",
        help="Affiche toutes les commandes disponibles avec leurs descriptions en Markdown (paginé)."
    )
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_commandes(self, ctx: commands.Context):
        try:
            pages = self.build_markdown_pages()
            for p in pages:
                await safe_send(ctx.channel, f"```md\n{p}\n```")
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !commandes] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Commandes(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
