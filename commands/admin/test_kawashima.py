# ────────────────────────────────────────────────────────────────────────────────
# 📌 test_kawashima_menu.py — Commande /testgame et !testgame avec sélection interactive
# Objectif : Tester un mini-jeu précis via menu déroulant paginé
# Catégorie : Autre
# Accès : Tous
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
import inspect
from utils import kawashima_games
import asyncio
import math

# ────────────────────────────────────────────────────────────────────────────────
# Commande
# ────────────────────────────────────────────────────────────────────────────────
class TestKawashimaMenu(commands.Cog):
    """Tester n’importe quel mini-jeu Kawashima via menu interactif paginé."""

    PAGE_SIZE = 10  # Nombre de jeux par page

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.games = {}
        for name, func in inspect.getmembers(kawashima_games, inspect.iscoroutinefunction):
            if not name.startswith("_"):
                title = getattr(func, "title", func.__name__)
                self.games[title] = func

    # ─────────── Commande texte ───────────
    @commands.command(name="testgame", aliases=["tg"], help="Tester un mini-jeu via menu interactif")
    async def testgame_cmd(self, ctx: commands.Context):
        await self.launch_menu(ctx)

    # ─────────── Commande slash ───────────
    @app_commands.command(name="testgame", description="Tester un mini-jeu via menu interactif")
    async def testgame_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.launch_menu(interaction)

    # ─────────── Lancer le menu paginé ───────────
    async def launch_menu(self, ctx_or_interaction):
        titles = list(self.games.keys())
        pages = [titles[i:i + self.PAGE_SIZE] for i in range(0, len(titles), self.PAGE_SIZE)]
        page_index = 0

        async def get_embed(page_idx):
            embed = discord.Embed(
                title="🧪 Testez un mini-jeu",
                description=f"Page {page_idx + 1}/{len(pages)} — Sélectionne un mini-jeu",
                color=discord.Color.blurple()
            )
            embed.add_field(
                name="Mini-jeux disponibles",
                value="\n".join([f"{i+1}. {title}" for i, title in enumerate(pages[page_idx])]),
                inline=False
            )
            return embed

        class MenuView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.selected_game = None
                self.page_idx = page_index

                # SelectMenu pour les mini-jeux
                options = [discord.SelectOption(label=title, value=title) for title in pages[self.page_idx]]
                self.select = discord.ui.Select(placeholder="Choisis un mini-jeu", options=options, row=0)
                self.select.callback = self.select_callback
                self.add_item(self.select)

                # Boutons pour pagination
                self.prev_btn = discord.ui.Button(label="◀️", style=discord.ButtonStyle.secondary)
                self.prev_btn.callback = self.prev_page
                self.next_btn = discord.ui.Button(label="▶️", style=discord.ButtonStyle.secondary)
                self.next_btn.callback = self.next_page
                self.add_item(self.prev_btn)
                self.add_item(self.next_btn)

                self.event = asyncio.Event()

            async def select_callback(self, interaction: discord.Interaction):
                self.selected_game = self.select.values[0]
                self.event.set()
                await interaction.response.defer()

            async def prev_page(self, interaction: discord.Interaction):
                if self.page_idx > 0:
                    self.page_idx -= 1
                    await self.update_page(interaction)

            async def next_page(self, interaction: discord.Interaction):
                if self.page_idx < len(pages) - 1:
                    self.page_idx += 1
                    await self.update_page(interaction)

            async def update_page(self, interaction):
                options = [discord.SelectOption(label=title, value=title) for title in pages[self.page_idx]]
                self.select.options = options
                embed = await get_embed(self.page_idx)
                await interaction.response.edit_message(embed=embed, view=self)

        view = MenuView()
        embed = await get_embed(page_index)

        if isinstance(ctx_or_interaction, discord.Interaction):
            msg = await ctx_or_interaction.followup.send(embed=embed, view=view)
        else:
            msg = await ctx_or_interaction.send(embed=embed, view=view)

        # Attente de la sélection
        await view.event.wait()
        await msg.edit(view=None)

        game_name = view.selected_game
        game = self.games.get(game_name)
        if not game:
            return

        # ─────────── Lancer le jeu choisi ───────────
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
    cog = TestKawashimaMenu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
