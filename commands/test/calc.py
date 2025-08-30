# ────────────────────────────────────────────────────────────────────────────────
# 📌 scientific_calculator_interactive.py — Calculatrice scientifique interactive
# Objectif : Calculatrice scientifique interactive avec mini-clavier Discord
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

from utils.discord_utils import safe_send, safe_edit, safe_respond  

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue de la calculatrice
# ────────────────────────────────────────────────────────────────────────────────
class CalculatorView(View):
    def __init__(self):
        super().__init__(timeout=180)
        self.expression = ""
        self.result = None
        self.update_buttons()

    def update_buttons(self):
        """Ajoute les boutons du mini-clavier scientifique"""
        self.clear_items()
        buttons = [
            ["7", "8", "9", "/", "sqrt"],
            ["4", "5", "6", "*", "^"],
            ["1", "2", "3", "-", "log"],
            ["0", ".", "(", ")", "+"],
            ["sin", "cos", "tan", "ln", "exp"],
            ["π", "e", "!", "C", "="]
        ]
        for row in buttons:
            for btn_label in row:
                self.add_item(CalcButton(btn_label, self))

class CalcButton(Button):
    def __init__(self, label, parent_view: CalculatorView):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        label = self.label
        view = self.parent_view

        if label == "C":
            view.expression = ""
            view.result = None
        elif label == "=":
            try:
                expr = view.expression.replace("π", str(math.pi)).replace("e", str(math.e))
                expr = expr.replace("^", "**").replace("sqrt", "math.sqrt").replace("log", "math.log10")
                expr = expr.replace("ln", "math.log").replace("sin", "math.sin(math.radians(").replace("cos", "math.cos(math.radians(").replace("tan", "math.tan(math.radians(")
                expr = expr.replace("!", "math.factorial(")
                # fermer les parenthèses pour fonctions trig/factorielle
                open_funcs = expr.count("(")
                close_parens = expr.count(")")
                expr += ")" * (open_funcs - close_parens)
                view.result = eval(expr)
                view.expression = str(view.result)
            except Exception as e:
                view.result = f"Erreur : {e}"
                view.expression = ""
        else:
            view.expression += label if label not in ["sin","cos","tan","!"] else label+"("
        await safe_edit(interaction.message, content=f"🧮 Expression : `{view.expression}`\n📊 Résultat : `{view.result}`", view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ScientificCalculatorInteractive(commands.Cog):
    """
    Commande /calc et !calc — Calculatrice scientifique interactive avec mini-clavier
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_calculator(self, channel: discord.abc.Messageable):
        view = CalculatorView()
        view.message = await safe_send(channel, "🧮 Calculatrice scientifique interactive :", view=view)

    @app_commands.command(name="calc", description="Calculatrice scientifique interactive")
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
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !calc] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ScientificCalculatorInteractive(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
