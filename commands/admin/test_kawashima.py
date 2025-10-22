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
import inspect
from utils import kawashima_games
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
PAGE_SIZE = 10

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

    # ─────────── Commande SLASH ───────────
    @app_commands.command(
        name="testgame",
        description="Tester un mini-jeu de l'entraînement cérébral via son numéro ou afficher la liste."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_testgame(self, interaction: discord.Interaction, choice: str = None):
        await interaction.response.defer()
        await self.run_game(interaction, choice)

    # ─────────── Commande PREFIX ───────────
    @commands.command(name="testgame", aliases=["tg"], help="Tester un mini-jeu de l'entraînement cérébral via son numéro ou afficher la liste.")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_testgame(self, ctx: commands.Context, choice: str = None):
        await self.run_game(ctx, choice)

    # ─────────── Lancer le mini-jeu ───────────
    async def run_game(self, ctx_or_interaction, choice: str | int = None):
        # ─────────── Pagination si aucun choix ───────────
        if choice is None:
            pages = [
                self.sorted_titles[i:i + PAGE_SIZE]
                for i in range(0, len(self.sorted_titles), PAGE_SIZE)
            ]
            current_page = 0

            class PageView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                    self.page = current_page
                    self.message = None

                @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
                async def prev(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.page = (self.page - 1) % len(pages)
                    await self.update(interaction)

                @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
                async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                    self.page = (self.page + 1) % len(pages)
                    await self.update(interaction)

                async def update(self, interaction):
                    page_text = "\n".join(
                        f"{i + 1 + self.page*PAGE_SIZE}. {title}" for i, title in enumerate(pages[self.page])
                    )
                    embed = discord.Embed(
                        title=f"🧪 Liste des mini-jeux — Page {self.page+1}/{len(pages)}",
                        description=page_text,
                        color=discord.Color.blurple()
                    )
                    await interaction.response.edit_message(embed=embed, view=self)

            page_view = PageView()
            page_text = "\n".join(f"{i+1}. {title}" for i, title in enumerate(pages[current_page]))
            embed = discord.Embed(
                title=f"🧪 Liste des mini-jeux — Page 1/{len(pages)}",
                description=page_text,
                color=discord.Color.blurple()
            )
            if isinstance(ctx_or_interaction, discord.Interaction):
                page_view.message = await ctx_or_interaction.followup.send(embed=embed, view=page_view)
            else:
                page_view.message = await ctx_or_interaction.send(embed=embed, view=page_view)
            return

        # ─────────── Tester tous les jeux si "all" ───────────
        if isinstance(choice, str) and choice.lower() == "all":
            for i, game_name in enumerate(self.sorted_titles, start=1):
                game = self.games[game_name]
                if isinstance(ctx_or_interaction, discord.Interaction):
                    send = ctx_or_interaction.followup.send
                    user = ctx_or_interaction.user
                else:
                    send = ctx_or_interaction.send
                    user = ctx_or_interaction.author

                game_embed = discord.Embed(
                    title=f"🧪 Mini-jeu {i}/{len(self.sorted_titles)} : {game_name}",
                    description="Réponds dans le chat pour jouer !",
                    color=discord.Color.blurple()
                )
                game_msg = await send(embed=game_embed)
                try:
                    success = await game(game_msg, game_embed, lambda: user.id, self.bot)
                    result_text = "✅ Bien joué !" if success else "❌ Raté !"
                except Exception as e:
                    result_text = f"⚠️ Erreur lors du test : {e}"

                result_embed = discord.Embed(
                    title=f"Résultat — {game_name}",
                    description=result_text,
                    color=discord.Color.green() if success else discord.Color.red()
                )
                await send(embed=result_embed)
            return

        # ─────────── Vérification du numéro ───────────
        if not 1 <= int(choice) <= len(self.sorted_titles):
            msg = f"⚠️ Numéro invalide ! Choisis entre 1 et {len(self.sorted_titles)}"
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.followup.send(msg)
            else:
                await ctx_or_interaction.send(msg)
            return

        game_name = self.sorted_titles[int(choice) - 1]
        game = self.games[game_name]

        if isinstance(ctx_or_interaction, discord.Interaction):
            send = ctx_or_interaction.followup.send
            user = ctx_or_interaction.user
        else:
            send = ctx_or_interaction.send
            user = ctx_or_interaction.author

        game_embed = discord.Embed(
            title=f"🧪 Mini-jeu : {game_name}",
            description="Réponds dans le chat pour jouer !",
            color=discord.Color.blurple()
        )
        game_msg = await send(embed=game_embed)
        try:
            success = await game(game_msg, game_embed, lambda: user.id, self.bot)
            result_text = "✅ Bien joué !" if success else "❌ Raté !"
        except Exception as e:
            result_text = f"⚠️ Erreur lors du test : {e}"

        result_embed = discord.Embed(
            title=f"Résultat — {game_name}",
            description=result_text,
            color=discord.Color.green() if success else discord.Color.red()
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
