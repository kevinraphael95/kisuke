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

from utils.discord_utils import safe_send, safe_edit, safe_respond  

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Mini-clavier interactif
# ────────────────────────────────────────────────────────────────────────────────
class CalculatorView(View):
    def __init__(self):
        super().__init__(timeout=180)
        self.expression = ""
        self.result = None
        self.add_buttons()

    def add_buttons(self):
        rows = [
            ["7","8","9","/","sqrt"],
            ["4","5","6","*","^"],
            ["1","2","3","-","ln"],
            ["0",".","C","+","log"],
            ["sin","cos","tan","!","="]
        ]
        for row in rows:
            for label in row:
                self.add_item(CalcButton(label, self))

class CalcButton(Button):
    def __init__(self, label, parent_view):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        # ✅ Accuser réception pour éviter "Échec de l’interaction"
        await interaction.response.defer()

        view = self.parent_view
        label = self.label

        if label == "C":
            view.expression = ""
            view.result = None

        elif label == "=":
            try:
                expr = (
                    view.expression
                    .replace("π", str(math.pi))
                    .replace("e", str(math.e))
                    .replace("^", "**")
                )
                funcs = {
                    "sqrt": "math.sqrt",
                    "log": "math.log10",
                    "ln": "math.log",
                    "sin": "math.sin(math.radians",
                    "cos": "math.cos(math.radians",
                    "tan": "math.tan(math.radians",
                    "!": "math.factorial"
                }
                for k, v in funcs.items():
                    expr = expr.replace(k+"(", v+"(")
                # Équilibrer les parenthèses si manquantes
                open_parens = expr.count("(")
                close_parens = expr.count(")")
                expr += ")" * (open_parens - close_parens)

                # Calcul sécurisé
                view.result = eval(expr, {"math": math, "__builtins__": {}})
                # ✅ Après =, le résultat devient la nouvelle expression
                view.expression = str(view.result)

            except Exception:
                view.result = "Erreur"
                # On garde l'expression pour que l'utilisateur voie ce qu'il a tapé

        else:
            if label in ["sin","cos","tan","sqrt","log","ln","!"]:
                view.expression += label + "("
            else:
                view.expression += label

        # Affichage
        await safe_edit(
            interaction.message,
            content=(
                "╔══════════════════════════╗\n"
                f"║ = {view.result if view.result is not None else ''}\n"
                f"║ {view.expression or ''}\n"
                f"╚══════════════════════════╝"
            ),
            view=view
        )


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ScientificCalculator(commands.Cog):
    """
    Commande /calc et !calc — Calculatrice scientifique interactive avec mini-clavier
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Envoi du mini-clavier avec écran vide
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_calculator(self, channel: discord.abc.Messageable):
        view = CalculatorView()
        screen = (
            "╔══════════════════════════╗\n"
            "║ = \n"
            "║ \n"
            "╚══════════════════════════╝"
        )
        view.message = await safe_send(channel, screen, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
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

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
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
    cog = ScientificCalculator(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)



