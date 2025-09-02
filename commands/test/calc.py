# ────────────────────────────────────────────────────────────────────────────────
# 📌 scientific_calculator.py — Calculatrice scientifique interactive
# Objectif : Calculatrice scientifique interactive avec mini-clavier et fonctions avancées
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
from discord.ui import View, Button
import math
import re

from utils.discord_utils import safe_send, safe_edit, safe_respond  

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Évaluation sécurisée globale
# ────────────────────────────────────────────────────────────────────────────────
def safe_eval(expr: str):
    """Évalue une expression scientifique de manière sécurisée."""
    expr = expr.replace("^", "**").replace("π", str(math.pi)).replace("e", str(math.e))
    expr = re.sub(r"(\d+)!","math.factorial(\\1)", expr)

    funcs = {
        "sin": "math.sin(math.radians",
        "cos": "math.cos(math.radians",
        "tan": "math.tan(math.radians",
        "sqrt": "math.sqrt",
        "log": "math.log10",
        "ln": "math.log"
    }

    for k, v in funcs.items():
        expr = re.sub(rf"{k}\(", v+"(", expr)

    # Équilibrer les parenthèses
    open_parens = expr.count("(")
    close_parens = expr.count(")")
    expr += ")" * (open_parens - close_parens)

    return eval(expr, {"math": math, "__builtins__": {}})


# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Mini-clavier interactif
# ────────────────────────────────────────────────────────────────────────────────
class CalculatorView(View):
    def __init__(self):
        super().__init__(timeout=300)
        self.expression = ""
        self.result = None
        self.add_buttons()

    def add_buttons(self):
        rows = [
            ["7","8","9","/","sqrt"],
            ["4","5","6","*","^"],
            ["1","2","3","-","("],
            ["0",".","C","+"," )"],
            ["sin","cos","tan","ln","log"],
            ["!","π","e","="]
        ]
        for row in rows:
            for label in row:
                self.add_item(CalcButton(label, self))


class CalcButton(Button):
    def __init__(self, label, parent_view):
        super().__init__(label=label.strip(), style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = self.parent_view
        label = self.label

        if label == "C":
            view.expression = ""
            view.result = None
        elif label == "=":
            try:
                view.result = safe_eval(view.expression)
                view.expression = str(view.result)
            except Exception:
                view.result = "Erreur"
        else:
            view.expression += label

        screen = (
            "╔══════════════════════════╗\n"
            f"║ {view.expression or ''}\n"
            f"║ = {view.result if view.result is not None else ''}\n"
            "╚══════════════════════════╝"
        )

        # Mise à jour du message directement pour éviter safe_edit si problème
        await interaction.message.edit(content=screen, view=view)


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ScientificCalculator(commands.Cog):
    """Commande /calc et !calc — Calculatrice scientifique interactive"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_calculator(self, channel: discord.abc.Messageable):
        view = CalculatorView()
        screen = (
            "╔══════════════════════════╗\n"
            "║ \n"
            "║ = \n"
            "╚══════════════════════════╝"
        )
        # On utilise edit du message directement
        await channel.send(content=screen, view=view)

    @app_commands.command(
        name="calc",
        description="Calculatrice scientifique interactive"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_calc(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._send_calculator(interaction.channel)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /calc] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="calc")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_calc(self, ctx: commands.Context):
        try:
            await self._send_calculator(ctx.channel)
        except commands.CommandOnCooldown as e:
            await ctx.send(f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !calc] {e}")
            await ctx.send("❌ Une erreur est survenue.")


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ScientificCalculator(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
