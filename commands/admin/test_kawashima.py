# ────────────────────────────────────────────────────────────────────────────────
# 📌 test_kawashima_paginated.py — Tester un mini-jeu par numéro avec pagination
# Objectif : Lister tous les mini-jeux par ordre alphabétique, paginer si besoin, et les tester
# Catégorie : Autre
# Accès : Tous
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import inspect
from utils import kawashima_games
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# Paramètres
# ────────────────────────────────────────────────────────────────────────────────
PAGE_SIZE = 10  # nombre de jeux par page

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Commandes
# ────────────────────────────────────────────────────────────────────────────────
class TestKawashimaPaginated(commands.Cog):
    """Tester n’importe quel mini-jeu Kawashima via numéro avec pagination."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.games = {}
        for name, func in inspect.getmembers(kawashima_games, inspect.iscoroutinefunction):
            if not name.startswith("_"):
                title = getattr(func, "title", func.__name__)
                self.games[title] = func
        self.sorted_titles = sorted(self.games.keys())

    @commands.command(name="testgame", aliases=["tg"], help="Tester un mini-jeu par numéro")
    async def testgame_cmd(self, ctx: commands.Context, choice: int = None):
        await self.run_game(ctx, choice)

    async def run_game(self, ctx_or_interaction, choice: int = None):
        if choice is None:
            # ─────────── Pagination ───────────
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

        # ─────────── Vérification et lancement du jeu ───────────
        if not 1 <= choice <= len(self.sorted_titles):
            msg = f"⚠️ Numéro invalide ! Choisis entre 1 et {len(self.sorted_titles)}"
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.followup.send(msg)
            else:
                await ctx_or_interaction.send(msg)
            return

        game_name = self.sorted_titles[choice - 1]
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
# 🔌 Setup
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TestKawashimaPaginated(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)

