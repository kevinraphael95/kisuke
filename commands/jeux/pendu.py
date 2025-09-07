# ────────────────────────────────────────────────────────────────────────────────
# 📌 pendu.py — Commande interactive !pendu
# Objectif : Jeu du pendu interactif avec propositions par message
# Catégorie : Jeux
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import aiohttp
from utils.discord_utils import safe_send, safe_edit, safe_respond  # ✅ Utilisation safe_

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Constantes et ASCII
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

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Classe PenduGame
# ────────────────────────────────────────────────────────────────────────────────
class PenduGame:
    def __init__(self, mot: str):
        self.mot = mot.lower()
        self.trouve = set()
        self.rate = set()
        self.terminee = False
        self.max_erreurs = min(len(mot) + 1, MAX_ERREURS)

    def get_display_word(self) -> str:
        return " ".join([l if l in self.trouve else "_" for l in self.mot])

    def get_pendu_ascii(self) -> str:
        return PENDU_ASCII[min(len(self.rate), self.max_erreurs)]

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
        embed.add_field(name="Erreurs", value=f"`{len(self.rate)} / {self.max_erreurs}`", inline=False)
        embed.add_field(name="Lettres tentées", value=f"`{self.get_lettres_tentees()}`", inline=False)
        embed.set_footer(text="✉️ Propose une lettre en répondant par un message contenant UNE lettre.")
        return embed

    def propose_lettre(self, lettre: str):
        lettre = lettre.lower()
        if lettre in self.trouve or lettre in self.rate:
            return None

        if lettre in self.mot:
            self.trouve.add(lettre)
        else:
            self.rate.add(lettre)

        if all(l in self.trouve for l in set(self.mot)):
            self.terminee = True
            return "gagne"

        if len(self.rate) >= self.max_erreurs:
            self.terminee = True
            return "perdu"

        return "continue"

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Classe PenduSession (pour solo et multi)
# ────────────────────────────────────────────────────────────────────────────────
class PenduSession:
    def __init__(self, game: PenduGame, message: discord.Message, mode: str = "solo"):
        self.game = game
        self.message = message
        self.mode = mode  # "solo" ou "multi"
        self.players = set() if mode == "multi" else None  # uniquement multi

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Pendu(commands.Cog):
    """
    Commande !pendu — Jeu du pendu interactif, mode solo ou multi.
    """

    CATEGORIES = {"animaux": 19}  # → facile à étendre

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions = {}  # dict channel_id -> PenduSession
        self.http_session = aiohttp.ClientSession()

    @commands.command(
        name="pendu",
        help="Démarre une partie du jeu du pendu.",
        description="Lance une partie, puis propose des lettres par message."
    )
    async def pendu_cmd(self, ctx: commands.Context, mode: str = "solo"):
        channel_id = ctx.channel.id
        if channel_id in self.sessions:
            await safe_send(ctx.channel, "❌ Une partie est déjà en cours dans ce salon.")
            return

        mot = await self._fetch_random_word()
        if not mot:
            await safe_send(ctx.channel, "❌ Impossible de récupérer un mot, réessaie plus tard.")
            return

        game = PenduGame(mot)
        embed = game.create_embed()
        message = await safe_send(ctx.channel, embed=embed)

        session = PenduSession(game, message, mode)
        if mode == "multi":
            session.players.add(ctx.author.id)
        self.sessions[channel_id] = session

        await safe_send(ctx.channel, f"✅ Partie démarrée en mode **{mode}** !")

    async def _fetch_random_word(self) -> str | None:
        url = f"https://trouve-mot.fr/api/categorie/{self.CATEGORIES['animaux']}/1"
        try:
            async with self.http_session.get(url) as resp:
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

        channel_id = message.channel.id
        session: PenduSession = self.sessions.get(channel_id)
        if not session:
            return

        if session.mode == "solo" and message.author.id not in session.players and session.players is not None:
            # Solo : seulement le joueur initial
            if message.author.id not in session.players:
                return

        content = message.content.strip().lower()
        if len(content) != 1 or not content.isalpha():
            return

        game = session.game
        resultat = game.propose_lettre(content)

        if resultat is None:
            await safe_send(message.channel, f"❌ Lettre `{content}` déjà proposée.", delete_after=5)
            await message.delete()
            return

        embed = game.create_embed()
        try:
            await safe_edit(session.message, embed=embed)
        except discord.NotFound:
            del self.sessions[channel_id]
            await safe_send(message.channel, "❌ Partie annulée car le message du jeu a été supprimé.")
            return

        await message.delete()

        if resultat == "gagne":
            await safe_send(message.channel, f"🎉 Bravo {message.author.mention}, le mot `{game.mot}` a été deviné !")
            del self.sessions[channel_id]
            return

        if resultat == "perdu":
            await safe_send(message.channel, f"💀 Partie terminée ! Le mot était `{game.mot}`.")
            del self.sessions[channel_id]
            return

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Pendu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
