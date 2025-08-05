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
from utils.discord_utils import safe_send, safe_edit  # ✅ Utilisation safe_

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

    def get_lettres_tentees(self) -> str:
        lettres_tentees = sorted(self.trouve | self.rate)
        return ", ".join(lettres_tentees) if lettres_tentees else "Aucune"

    def create_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🕹️ Jeu du Pendu",
            description=f"```\n{self.get_pendu_ascii()}\n```",
            color=discord.Color.blue()
        )
        embed.add_field(name="Mot", value=f"`{self.get_display_word()}`", inline=False)
        embed.add_field(name="Erreurs", value=f"`{len(self.rate)} / {MAX_ERREURS}`", inline=False)
        embed.add_field(name="Lettres tentées", value=f"`{self.get_lettres_tentees()}`", inline=False)
        embed.set_footer(text="✉️ Propose une lettre en répondant par un message contenant UNE lettre.")
        return embed

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
        self.games = {}  # dict user_id -> dict {game: PenduGame, message: discord.Message}

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
        embed = game.create_embed()
        message = await safe_send(ctx.channel, embed=embed)
        self.games[ctx.author.id] = {"game": game, "message": message}

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

        user_data = self.games.get(message.author.id)
        if not user_data:
            return

        content = message.content.strip().lower()
        if len(content) != 1 or not content.isalpha():
            return  # On attend une seule lettre

        game: PenduGame = user_data["game"]
        resultat = game.propose_lettre(content)

        if resultat is None:
            # Lettre déjà proposée
            await safe_send(message.channel, f"❌ Lettre `{content}` déjà proposée.", delete_after=5)
            await message.delete()
            return

        # Mise à jour de l'embed dans le même message
        embed = game.create_embed()
        try:
            await safe_edit(user_data["message"], embed=embed)
        except discord.NotFound:
            # Message supprimé, on supprime la partie
            del self.games[message.author.id]
            await safe_send(message.channel, "❌ Partie annulée car le message du jeu a été supprimé.")
            return

        await message.delete()

        if resultat == "gagne":
            await safe_send(message.channel, f"🎉 Bravo {message.author.mention}, tu as deviné le mot `{game.mot}` !")
            del self.games[message.author.id]
            return

        if resultat == "perdu":
            await safe_send(message.channel, f"💀 Partie terminée ! Le mot était `{game.mot}`.")
            del self.games[message.author.id]
            return

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Pendu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
