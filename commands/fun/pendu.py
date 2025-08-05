# ────────────────────────────────────────────────────────────────────────────────
# 📌 pendu.py — Commande interactive !pendu
# Objectif : Jeu du pendu simple avec propositions de lettres par message
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import aiohttp
from utils.discord_utils import safe_send  # ✅ Utilisation safe_

# ────────────────────────────────────────────────────────────────────────────────
# 🎲 Classe PenduGame - logique du jeu
# ────────────────────────────────────────────────────────────────────────────────
PENDU_ASCII = [
    "`     \n     \n     \n     \n     \n=========`",
    "`     +---+\n     |   |\n         |\n         |\n         |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n         |\n         |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n     |   |\n         |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n    /|   |\n         |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n    /|\\  |\n         |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n    /|\\  |\n    /    |\n     =========`",
    "`     +---+\n     |   |\n     O   |\n    /|\\  |\n    / \\  |\n     =========`",
]

MAX_ERREURS = 7

class PenduGame:
    def __init__(self, mot: str):
        self.mot = mot.lower()
        self.trouve = set()
        self.rate = set()
        self.terminee = False

    def get_display_word(self) -> str:
        return " ".join([l if l in self.trouve else "_" for l in self.mot])

    def get_pendu_ascii(self) -> str:
        return PENDU_ASCII[min(len(self.rate), MAX_ERREURS)]

    def get_status_message(self) -> str:
        lettres_tentees = sorted(self.trouve | self.rate)
        lettres_str = ", ".join(lettres_tentees) if lettres_tentees else "Aucune"
        return (
            f"🕹️ **Jeu du Pendu**\n"
            f"{self.get_pendu_ascii()}\n\n"
            f"🔤 Mot : `{self.get_display_word()}`\n"
            f"❌ Erreurs : `{len(self.rate)} / {MAX_ERREURS}`\n"
            f"📛 Lettres tentées : `{lettres_str}`\n\n"
            f"✉️ Propose une lettre en répondant simplement par un message contenant UNE lettre."
        )

    def propose_lettre(self, lettre: str):
        lettre = lettre.lower()
        if lettre in self.trouve or lettre in self.rate:
            return None  # lettre déjà proposée

        if lettre in self.mot:
            self.trouve.add(lettre)
        else:
            self.rate.add(lettre)

        # Vérification victoire
        if all(l in self.trouve for l in set(self.mot)):
            self.terminee = True
            return "gagne"

        # Vérification défaite
        if len(self.rate) >= MAX_ERREURS:
            self.terminee = True
            return "perdu"

        return "continue"

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Pendu(commands.Cog):
    """
    Commande !pendu — Jeu du pendu simple, propose les lettres par message.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.games = {}  # dict user_id -> PenduGame

    @commands.command(
        name="pendu",
        help="Démarre une partie du jeu du pendu.",
        description="Lance une partie, puis propose des lettres en répondant par message."
    )
    async def pendu(self, ctx: commands.Context):
        if ctx.author.id in self.games:
            await safe_send(ctx.channel, "❌ Tu as déjà une partie en cours.")
            return

        mot = await self._fetch_random_word()
        if not mot:
            await safe_send(ctx.channel, "❌ Impossible de récupérer un mot, réessaie plus tard.")
            return

        game = PenduGame(mot)
        self.games[ctx.author.id] = game
        await safe_send(ctx.channel, game.get_status_message())

    async def _fetch_random_word(self) -> str | None:
        url = "https://trouve-mot.fr/api/categorie/19/1"  # Animaux
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    return data[0]["name"].lower()
        except Exception:
            return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        game = self.games.get(message.author.id)
        if not game:
            return

        content = message.content.strip().lower()
        if len(content) != 1 or not content.isalpha():
            return  # On attend une seule lettre

        resultat = game.propose_lettre(content)
        if resultat is None:
            # Lettre déjà proposée
            await safe_send(message.channel, f"❌ Lettre `{content}` déjà proposée.", delete_after=5)
            await message.delete()
            return

        if resultat == "gagne":
            await safe_send(message.channel, f"🎉 Bravo {message.author.mention}, tu as deviné le mot `{game.mot}` !")
            del self.games[message.author.id]
            await message.delete()
            return

        if resultat == "perdu":
            await safe_send(message.channel, f"💀 Partie terminée ! Le mot était `{game.mot}`.")
            del self.games[message.author.id]
            await message.delete()
            return

        # Partie continue
        await safe_send(message.channel, game.get_status_message())
        await message.delete()

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Pendu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
