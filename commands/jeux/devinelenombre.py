# ────────────────────────────────────────────────────────────────────────────────
# 📌 justeprix.py — Commande interactive /justeprix et !justeprix
# Objectif : Jeu du Juste Prix, deviner un nombre entre 0 et 100
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, TextInput, Modal
import random
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Modal pour proposer un nombre
# ────────────────────────────────────────────────────────────────────────────────
class JustePrixModal(Modal):
    def __init__(self, parent_view):
        super().__init__(title="Propose un nombre")
        self.parent_view = parent_view
        self.number_input = TextInput(
            label="Nombre entre 0 et 100",
            placeholder="Exemple : 42",
            required=True,
            max_length=3,
            min_length=1
        )
        self.add_item(self.number_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            guess = int(self.number_input.value.strip())
        except ValueError:
            return await interaction.response.send_message("❌ Ce n'est pas un nombre valide.", ephemeral=True)
        await self.parent_view.process_guess(interaction, guess)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue principale avec boutons
# ────────────────────────────────────────────────────────────────────────────────
class JustePrixView(View):
    def __init__(self, target: int, max_attempts: int = 10, author_id: int | None = None):
        super().__init__(timeout=180)
        self.target = target
        self.max_attempts = max_attempts
        self.attempts: list[int] = []
        self.message = None
        self.finished = False
        self.author_id = author_id
        self.add_item(JustePrixButton(self))

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎯 Juste Prix",
            description=f"Devine le nombre entre 0 et 100",
            color=discord.Color.orange()
        )
        if self.attempts:
            lines = []
            for idx, val in enumerate(self.attempts, 1):
                if val < self.target:
                    symbol = "⬆️ Trop bas"
                elif val > self.target:
                    symbol = "⬇️ Trop haut"
                else:
                    symbol = "✅ Exact !"
                lines.append(f"{idx}. {val} → {symbol}")
            embed.add_field(name=f"Essais ({len(self.attempts)}/{self.max_attempts})", value="\n".join(lines), inline=False)
        else:
            embed.add_field(name="Essais", value="*(Aucun essai pour l’instant)*", inline=False)

        if self.finished:
            if self.attempts and self.attempts[-1] == self.target:
                embed.color = discord.Color.green()
                embed.set_footer(text="🎉 Bravo ! Tu as trouvé le nombre.")
            else:
                embed.color = discord.Color.red()
                embed.set_footer(text=f"💀 Partie terminée. Le nombre était {self.target}.")

        return embed

    async def process_guess(self, interaction: discord.Interaction, guess: int):
        if self.finished:
            return await safe_respond(interaction, "⚠️ La partie est terminée.", ephemeral=True)
        if not (0 <= guess <= 100):
            return await safe_respond(interaction, "⚠️ Le nombre doit être entre 0 et 100.", ephemeral=True)

        self.attempts.append(guess)
        if guess == self.target or len(self.attempts) >= self.max_attempts:
            self.finished = True
            for child in self.children:
                child.disabled = True

        await safe_edit(self.message, embed=self.build_embed(), view=self)
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def on_timeout(self):
        if self.finished:
            return
        self.finished = True
        for child in self.children:
            child.disabled = True
        embed = self.build_embed()
        embed.color = discord.Color.red()
        embed.set_footer(text=f"⏳ Temps écoulé ! Le nombre était {self.target}.")
        await safe_edit(self.message, embed=embed, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Bouton Proposer
# ────────────────────────────────────────────────────────────────────────────────
class JustePrixButton(Button):
    def __init__(self, parent_view: JustePrixView):
        super().__init__(label="Proposer un nombre", style=discord.ButtonStyle.primary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.author_id and interaction.user.id != self.parent_view.author_id:
            return await interaction.response.send_message("❌ Seul le lanceur peut proposer un nombre.", ephemeral=True)
        await interaction.response.send_modal(JustePrixModal(self.parent_view))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class JustePrix(commands.Cog):
    """Commande /justeprix et !justeprix — Jeu du Juste Prix"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _start_game(self, channel: discord.abc.Messageable, author_id: int):
        target = random.randint(0, 100)
        view = JustePrixView(target, max_attempts=10, author_id=author_id)
        embed = view.build_embed()
        view.message = await safe_send(channel, embed=embed, view=view)

    @app_commands.command(name="devine_le_nombre", description="Jeu du Juste Prix : devine le nombre entre 0 et 100")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_justeprix(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._start_game(interaction.channel, author_id=interaction.user.id)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /justeprix] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="devine_le_nombre", aliases="dln", help="Jeu du Juste Prix : devine le nombre entre 0 et 100")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_justeprix(self, ctx: commands.Context):
        try:
            await self._start_game(ctx.channel, author_id=ctx.author.id)
        except Exception as e:
            print(f"[ERREUR !justeprix] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = JustePrix(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
