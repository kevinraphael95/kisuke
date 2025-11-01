# ────────────────────────────────────────────────────────────────────────────────
# 📌 test_kawashima.py — Tester un mini-jeu par numéro avec pagination
# Objectif : Lister tous les mini-jeux par ordre alphabétique, paginer si nécessaire et les tester facilement
# Catégorie : Admin
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import inspect, asyncio
from utils import kawashima_games
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Constantes
# ────────────────────────────────────────────────────────────────────────────────
PAGE_SIZE = 10

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class TestKawashima(commands.Cog):
    """
    Commande /testgame et !testgame — Tester n’importe quel mini-jeu Kawashima via numéro avec pagination.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.games = {}
        for name, func in inspect.getmembers(kawashima_games, inspect.iscoroutinefunction):
            if not name.startswith("_"):
                title = getattr(func, "title", func.__name__)
                self.games[title] = func
        self.sorted_titles = sorted(self.games.keys())

    # ──────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ──────────────────────────────────────────────────────────────
    @app_commands.command(
        name="testgame",
        description="Tester un mini-jeu de l'entraînement cérébral via son numéro ou afficher la liste."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_testgame(self, interaction: discord.Interaction, choix: str = None):
        await safe_respond(interaction, "Chargement du quizz...", ephemeral=True)
        await self.run_game(interaction, choix)

    # ──────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ──────────────────────────────────────────────────────────────
    @commands.command(name="testgame", aliases=["tg"], help="Tester un mini-jeu de l'entraînement cérébral via son numéro ou afficher la liste.")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_testgame(self, ctx: commands.Context, choix: str = None):
        await self.run_game(ctx, choix)

    # ──────────────────────────────────────────────────────────────
    # 🎮 Lancer le mini-jeu ou afficher la liste
    # ──────────────────────────────────────────────────────────────
    async def run_game(self, ctx_or_interaction, choix: str | int = None):
        """Affiche la liste paginée des mini-jeux ou lance celui choisi."""
        # Détermine les méthodes d’envoi et l’utilisateur
        if isinstance(ctx_or_interaction, discord.Interaction):
            send = lambda *a, **kw: safe_send(ctx_or_interaction.channel, *a, **kw)
            user = ctx_or_interaction.user
        else:
            send = lambda *a, **kw: safe_send(ctx_or_interaction, *a, **kw)
            user = ctx_or_interaction.author

        # ─────────── Pagination si aucun choix ───────────
        if choix is None:
            pages = [
                self.sorted_titles[i:i + PAGE_SIZE]
                for i in range(0, len(self.sorted_titles), PAGE_SIZE)
            ]

            class PageView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                    self.page = 0

                @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
                async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user != user:
                        return await interaction.response.send_message("❌ Ce menu ne t’est pas destiné.", ephemeral=True)
                    self.page = (self.page - 1) % len(pages)
                    await self.update(interaction)

                @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
                async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user != user:
                        return await interaction.response.send_message("❌ Ce menu ne t’est pas destiné.", ephemeral=True)
                    self.page = (self.page + 1) % len(pages)
                    await self.update(interaction)

                async def update(self, interaction: discord.Interaction):
                    page_text = "\n".join(
                        f"{i + 1 + self.page * PAGE_SIZE}. {title}"
                        for i, title in enumerate(pages[self.page])
                    )
                    embed = discord.Embed(
                        title=f"🧪 Liste des mini-jeux — Page {self.page + 1}/{len(pages)}",
                        description=page_text,
                        color=discord.Color.blurple()
                    )
                    await safe_edit(interaction.message, embed=embed, view=self)

            page_view = PageView()
            page_text = "\n".join(
                f"{i + 1}. {title}" for i, title in enumerate(pages[0])
            )
            embed = discord.Embed(
                title=f"🧪 Liste des mini-jeux — Page 1/{len(pages)}",
                description=page_text,
                color=discord.Color.blurple()
            )
            await send(embed=embed, view=page_view)
            return

        # ─────────── Vérification du numéro ───────────
        if not str(choix).isdigit() or not 1 <= int(choix) <= len(self.sorted_titles):
            return await send(f"⚠️ Numéro invalide ! Choisis entre **1** et **{len(self.sorted_titles)}**.")

        game_name = self.sorted_titles[int(choix) - 1]
        game_func = self.games[game_name]

        embed = discord.Embed(
            title=f"🧪 Mini-jeu : {game_name}",
            description="Réponds dans le chat pour jouer !",
            color=discord.Color.blurple()
        )
        game_msg = await send(embed=embed)

        try:
            success = await game_func(game_msg, embed, lambda: user.id, self.bot)
            result_text = "✅ Bien joué !" if success else "❌ Raté !"
            color = discord.Color.green() if success else discord.Color.red()
        except Exception as e:
            result_text = f"⚠️ Erreur lors du test : {e}"
            color = discord.Color.orange()

        result_embed = discord.Embed(
            title=f"Résultat — {game_name}",
            description=result_text,
            color=color
        )
        await send(embed=result_embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TestKawashima(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
