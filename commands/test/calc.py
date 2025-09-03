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
# 🧰 Helpers pour l'évaluation sécurisée et transformations
# ────────────────────────────────────────────────────────────────────────────────
def replace_factorials(expr: str) -> str:
    """
    Remplace occurrences simples 'NUMBER!' ou '(expr)!' par math.factorial(...) itérativement.
    (Gestion limitée aux parenthèses non imbriquées pour la robustesse simple.)
    """
    pattern = re.compile(r'(\d+|\([^()]*\))!')
    while True:
        m = pattern.search(expr)
        if not m:
            break
        group = m.group(1)
        expr = expr[:m.start()] + f"math.factorial({group})" + expr[m.end():]
    return expr

def replace_percentages(expr: str) -> str:
    """
    Remplace 'NUMBER%' par '(NUMBER/100)'.
    Ex: 50% -> (50/100)
    """
    return re.sub(r'(\d+(\.\d+)?)%', r'(\1/100)', expr)

def prepare_expression(raw: str, mode_deg: bool, last_answer):
    """
    Transforme l'expression du format 'affichage' vers une expression python-safe utilisable par eval.
    """
    expr = raw

    # tokens d'affichage -> python
    expr = expr.replace('×', '*').replace('÷', '/').replace('−', '-')
    # xʸ : on peut avoir ajouté '**' directement mais si on garde le label, remplace
    expr = expr.replace('xʸ', '**').replace('^', '**')

    # EXP : on utilisera 'E' comme notation scientifique (1EXP2 => 1E2)
    expr = expr.replace('EXP', 'E')

    # constantes (pi et la constante e)
    expr = expr.replace('π', 'math.pi')
    # Pour la constante e (si tu veux un bouton 'e' qui insère la constante), on utilisera math.e
    expr = expr.replace(' const_e ', 'math.e')  # placeholder, on n'utilise pas directement 'e' pour éviter collision

    # remplacer 'Ans' par la valeur numérique si disponible
    if 'Ans' in expr and last_answer is not None:
        expr = expr.replace('Ans', str(last_answer))

    # remplacer fonctions usuelles -> math.*
    expr = expr.replace('√(', 'math.sqrt(')
    expr = expr.replace('ln(', 'math.log(')
    expr = expr.replace('log(', 'math.log10(')

    # sin/cos/tan : on convertira les degrés si demandé en injectant math.radians(...)
    expr = expr.replace('sin(', 'math.sin(').replace('cos(', 'math.cos(').replace('tan(', 'math.tan(')
    if mode_deg:
        # injecter conversion degrés -> radians : math.sin(math.radians(...))
        expr = expr.replace('math.sin(math.radians(', 'math.sin(math.radians(')  # idempotent
        expr = expr.replace('math.cos(math.radians(', 'math.cos(math.radians(')
        expr = expr.replace('math.tan(math.radians(', 'math.tan(math.radians(')
        # Actually we need to wrap math.sin( .. ) arguments with math.radians(...)
        # Simple approach: replace 'math.sin(' by 'math.sin(math.radians(' then close parens more basiquement below.
        expr = expr.replace('math.sin(', 'math.sin(math.radians(')
        expr = expr.replace('math.cos(', 'math.cos(math.radians(')
        expr = expr.replace('math.tan(', 'math.tan(math.radians(')

    # factorial notation : replace occurrences like '5!' or '(2+3)!'
    expr = replace_factorials(expr)

    # pourcentages
    expr = replace_percentages(expr)

    # équilibrer parenthèses de façon simple
    open_p = expr.count('(')
    close_p = expr.count(')')
    if open_p > close_p:
        expr += ')' * (open_p - close_p)

    return expr

def safe_eval(expr: str):
    """
    Évalue expression dans un contexte limité.
    """
    try:
        # on expose seulement math et aucune builtin
        return eval(expr, {"math": math}, {})
    except Exception as e:
        # Propager l'erreur pour logging
        raise

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Views : page principale (Main) et page avancée (Advanced)
# ────────────────────────────────────────────────────────────────────────────────
class MainCalculatorView(View):
    def __init__(self):
        super().__init__(timeout=180)
        self.expression: str = ""
        self.result = None
        self.last_answer = None
        self.mode_deg = True  # par défaut en degrés
        self.message = None
        self.add_buttons()

    def add_buttons(self):
        # Chaque ligne = max 5 boutons (contrainte Discord). Total 5x5 = 25 boutons max.
        rows = [
            ["Mode", "x!", "(", ")", "AC"],
            ["sin", "cos", "tan", "ln", "log"],
            ["7", "8", "9", "÷", "√"],
            ["4", "5", "6", "×", "xʸ"],
            ["1", "2", "3", "−", "More"]
        ]
        for row_idx, row in enumerate(rows):
            for col_idx, label in enumerate(row):
                btn = MainCalcButton(label, self)
                # placer sur la ligne row_idx (pour organiser)
                btn.row = row_idx
                self.add_item(btn)

class AdvancedCalculatorView(View):
    def __init__(self, main_view: MainCalculatorView):
        super().__init__(timeout=180)
        # On garde une référence vers la MainView pour récupérer état (Ans, mode, last_answer)
        self.main = main_view
        self.expression = main_view.expression
        self.result = main_view.result
        self.last_answer = main_view.last_answer
        self.mode_deg = main_view.mode_deg
        self.message = None
        self.add_buttons()

    def add_buttons(self):
        rows = [
            ["Ans", "EXP", "π", "e", "%"],
            ["0", ".", "=", "+", "Back"]
        ]
        for row_idx, row in enumerate(rows):
            for col_idx, label in enumerate(row):
                btn = AdvCalcButton(label, self)
                btn.row = row_idx
                self.add_item(btn)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Boutons page principale
# ────────────────────────────────────────────────────────────────────────────────
class MainCalcButton(Button):
    def __init__(self, label, parent_view: MainCalculatorView):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view = self.parent_view
        label = self.label

        try:
            # Mode (toggle Deg/Rad)
            if label == "Mode":
                view.mode_deg = not view.mode_deg
                view.result = f"Mode : {'Deg' if view.mode_deg else 'Rad'}"

            # AC -> clear
            elif label == "AC":
                view.expression = ""
                view.result = None

            # More -> basculer vers la page avancée
            elif label == "More":
                adv = AdvancedCalculatorView(view)
                adv.message = interaction.message
                display = render_display(adv.expression, adv.result)
                await safe_edit(interaction.message, content=display, view=adv)
                return  # on termine la callback

            # Egal traite ici? Non, '=' est sur la page avancée
            elif label == "=":
                # si present; mais pour sécurité
                pass

            # Fonctions (on ajoute 'nom(' pour facilité)
            elif label in ["sin", "cos", "tan", "ln", "log", "√"]:
                token = label
                if label == "√":
                    token = "√("
                else:
                    token = label + "("
                view.expression += token

            # Factorial token (on note '!' à la fin)
            elif label == "x!":
                view.expression += "!"

            # xʸ : on utilise '**'
            elif label == "xʸ":
                view.expression += "**"

            # Opérateurs et chiffres
            elif label in ["+", "−", "×", "÷", "(", ")"] or re.fullmatch(r'\d', label):
                # les chiffres et opérateurs s'ajoutent tels quels (pour plus tard remplacement)
                view.expression += label

            else:
                # fallback : concatène label
                view.expression += label

            # reset result if we appended something
            if label not in ["Mode"]:
                if view.result is not None and view.result != "Mode : Deg" and view.result != "Mode : Rad":
                    # si on avait un résultat, et qu'on ajoute un opérateur on commence nouveau calcul
                    # mais si on tape un opérateur, on veut souvent continuer depuis le résultat -> géré par utilisateur
                    view.result = None

            display = render_display(view.expression, view.result)
            await safe_edit(interaction.message, content=display, view=view)

        except Exception as e:
            # debug print pour voir l'erreur réelle dans les logs
            print(f"[ERREUR bouton main] {e}")
            await safe_edit(interaction.message, content="❌ Erreur interne (voir logs).", view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Boutons page avancée
# ────────────────────────────────────────────────────────────────────────────────
class AdvCalcButton(Button):
    def __init__(self, label, parent_view: AdvancedCalculatorView):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        adv = self.parent_view
        view = adv.main  # on écrira dans main_view pour garder l'état partagé
        label = self.label

        try:
            if label == "Back":
                # Retour à la page principale
                view.message = interaction.message
                display = render_display(view.expression, view.result)
                await safe_edit(interaction.message, content=display, view=view)
                return

            if label == "=":
                # Evaluate using main view state
                try:
                    prepared = prepare_expression(view.expression, view.mode_deg, view.last_answer)
                    # debug print
                    # print("Eval expr:", prepared)
                    val = safe_eval(prepared)
                    view.result = val
                    view.last_answer = val
                except Exception as ee:
                    print(f"[ERREUR éval] {ee}")
                    view.result = "Erreur"
                display = render_display(view.expression, view.result)
                await safe_edit(interaction.message, content=display, view=adv)
                return

            # Ans -> insérer le token 'Ans' (sera remplacé par last_answer lors de l'éval)
            if label == "Ans":
                if view.last_answer is not None:
                    view.expression += f"{view.last_answer}"
                else:
                    # rien à ajouter si pas d'Ans
                    pass

            # EXP -> notation scientifique : on ajoute 'E' (ex: 1EXP2 -> 1E2)
            elif label == "EXP":
                view.expression += "E"

            # π -> math.pi
            elif label == "π":
                view.expression += "math.pi"

            # e -> constante math.e
            elif label == "e":
                view.expression += "math.e"

            # % handled as a literal '%' and transformed in prepare_expression
            elif label == "%":
                view.expression += "%"

            # chiffres et opérateurs
            elif label in ["0", ".", "+", "="]:
                view.expression += label

            else:
                view.expression += label

            display = render_display(view.expression, view.result)
            await safe_edit(interaction.message, content=display, view=adv)

        except Exception as e:
            print(f"[ERREUR bouton adv] {e}")
            await safe_edit(interaction.message, content="❌ Erreur interne (voir logs).", view=adv)

# ────────────────────────────────────────────────────────────────────────────────
# 🖥️ Rendu écran (ASCII) — style Google façon console
# ────────────────────────────────────────────────────────────────────────────────
def render_display(expression: str, result) -> str:
    # Tronquer pour ne pas dépasser une longueur raisonnable
    expr_display = (expression or "")[:120]
    res_display = str(result) if result is not None else ""
    box_width = 38
    top = "╔" + "═" * box_width + "╗\n"
    mid_expr = f"║ {expr_display}\n"
    mid_res = f"║ = {res_display}\n"
    bot = "╚" + "═" * box_width + "╝"
    return top + mid_expr + mid_res + bot

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ScientificCalculator(commands.Cog):
    """
    Commande /calc et !calc — Calculatrice scientifique interactive avec mini-clavier
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_calculator(self, channel: discord.abc.Messageable):
        view = MainCalculatorView()
        screen = render_display(view.expression, view.result)
        view.message = await safe_send(channel, screen, view=view)

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
            command.category = "Utilitaire"
    await bot.add_cog(cog)


