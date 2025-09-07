# ────────────────────────────────────────────────────────────────────────────────
# 📌 1000bornes.py — Commande interactive 1000 Bornes
# Objectif : Jouer à 1000 Bornes solo ou multi-joueurs avec DM pour les mains
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
from discord.ui import View, Select
from utils.discord_utils import safe_send, safe_respond
import random
from typing import List, Optional

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Cartes et deck
# ────────────────────────────────────────────────────────────────────────────────
CARDS = {
    '25': {'type':'distance', 'km':25},
    '50': {'type':'distance', 'km':50},
    '75': {'type':'distance', 'km':75},
    '100': {'type':'distance', 'km':100},
    '200': {'type':'distance', 'km':200},
    'accident': {'type':'attack', 'name':'Accident'},
    'flat': {'type':'attack', 'name':'Crevaison'},
    'gas': {'type':'attack', 'name':'Panne d\'essence'},
    'stop': {'type':'attack', 'name':'Feu/Stop'},
    'speed': {'type':'attack', 'name':'Limitation de vitesse'},
    'repair': {'type':'parade', 'name':'Réparation'},
    'tire': {'type':'parade', 'name':'Roue de secours'},
    'fuel': {'type':'parade', 'name':'Essence'},
    'go': {'type':'parade', 'name':'Feu Vert'},
    'endlimit': {'type':'parade', 'name':'Fin de limitation'}
}

DECK_COUNTS = {
    '25':10, '50':10, '75':8, '100':8, '200':4,
    'accident':3, 'flat':3, 'gas':3, 'stop':5, 'speed':4,
    'repair':6, 'tire':6, 'fuel':6, 'go':8, 'endlimit':6
}

HAND_SIZE = 6
TARGET_KM = 1000

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Classes de jeu
# ────────────────────────────────────────────────────────────────────────────────
class Player:
    def __init__(self, user: discord.User):
        self.user = user
        self.hand: List[str] = []
        self.km = 0
        self.stopped = True

class Game:
    def __init__(self, channel: discord.TextChannel):
        self.channel = channel
        self.players: List[Player] = []
        self.deck: List[str] = self.build_deck()
        self.discard: List[str] = []
        self.current_index = 0

    def build_deck(self) -> List[str]:
        deck = []
        for card, count in DECK_COUNTS.items():
            deck.extend([card]*count)
        random.shuffle(deck)
        return deck

    def add_player(self, user: discord.User):
        self.players.append(Player(user))

    def draw(self) -> Optional[str]:
        if not self.deck:
            self.deck = self.discard[:]
            self.discard.clear()
            random.shuffle(self.deck)
        return self.deck.pop() if self.deck else None

    def deal(self):
        for p in self.players:
            for _ in range(HAND_SIZE):
                card = self.draw()
                if card:
                    p.hand.append(card)

    def next_player(self):
        self.current_index = (self.current_index + 1) % len(self.players)
        return self.players[self.current_index]

    def current_player(self):
        return self.players[self.current_index]

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI pour jouer une carte
# ────────────────────────────────────────────────────────────────────────────────
class PlaySelect(Select):
    def __init__(self, game: Game, player: Player):
        self.game = game
        self.player = player
        options = [discord.SelectOption(label=f"{c} ({CARDS[c].get('name', c)})", value=c) for c in player.hand]
        super().__init__(placeholder="Choisis une carte", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message("Ce n'est pas ton tour !", ephemeral=True)
            return

        card = self.values[0]
        self.player.hand.remove(card)
        self.game.discard.append(card)

        if CARDS[card]['type'] == 'distance':
            self.player.km += CARDS[card]['km']
        elif CARDS[card]['type'] == 'attack':
            next_p = self.game.next_player()
            next_p.stopped = True
        elif CARDS[card]['type'] == 'parade':
            self.player.stopped = False

        await interaction.response.send_message(f"✅ Tu as joué {card} ({CARDS[card].get('name', card)})", ephemeral=True)

        # Vérifie si le joueur a gagné
        if self.player.km >= TARGET_KM:
            await safe_send(self.game.channel, f"🏁 {self.player.user.mention} a atteint {TARGET_KM} km et gagne la partie !")
            del GAMES[self.game.channel.id]
            return

        next_player = self.game.next_player()
        await send_hand(next_player, self.game)

class PlayView(View):
    def __init__(self, game: Game, player: Player):
        super().__init__(timeout=120)
        self.add_item(PlaySelect(game, player))

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Fonction utilitaire pour envoyer la main en DM
# ────────────────────────────────────────────────────────────────────────────────
async def send_hand(player: Player, game: Game):
    if not player.user.dm_channel:
        await player.user.create_dm()
    view = PlayView(game, player)
    hand_text = "\n".join([f"{c} ({CARDS[c].get('name', c)})" for c in player.hand])
    await player.user.dm_channel.send(f"🎴 Ta main :\n{hand_text}\nChoisis une carte :", view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
GAMES = {}

class MilleBornes(commands.Cog):
    """
    Commande /1000 ou !1000 — Commence une partie solo ou multi 1000 Bornes
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH pour lancer une partie
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="1000",
        description="Commence une partie de 1000 Bornes (solo ou multi)"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_1000(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            await self.start_game(interaction.user, interaction.channel)
            await interaction.followup.send("✅ Partie commencée ! Check tes DM pour jouer.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /1000] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX pour lancer une partie
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="1000")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_1000(self, ctx: commands.Context):
        try:
            await self.start_game(ctx.author, ctx.channel)
            await safe_send(ctx.channel, "✅ Partie commencée ! Check tes DM pour jouer.")
        except Exception as e:
            print(f"[ERREUR !1000] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande pour voir les règles
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="regles1000",
        description="Affiche les règles du jeu 1000 Bornes"
    )
    async def slash_regles1000(self, interaction: discord.Interaction):
        rules = (
            "🎯 **Objectif :** atteindre 1000 km.\n"
            "🃏 **Cartes :** distance, attaque, parade.\n"
            "🚦 **Tours :** chaque joueur joue à son tour.\n"
            "✅ **Victoire :** premier joueur à atteindre 1000 km.\n"
            "💡 Les cartes sont envoyées en DM pour que seul le joueur voie sa main."
        )
        await safe_respond(interaction, rules, ephemeral=True)

    @commands.command(name="regles1000")
    async def prefix_regles1000(self, ctx: commands.Context):
        rules = (
            "🎯 **Objectif :** atteindre 1000 km.\n"
            "🃏 **Cartes :** distance, attaque, parade.\n"
            "🚦 **Tours :** chaque joueur joue à son tour.\n"
            "✅ **Victoire :** premier joueur à atteindre 1000 km.\n"
            "💡 Les cartes sont envoyées en DM pour que seul le joueur voie sa main."
        )
        await safe_send(ctx.channel, rules)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne pour lancer la partie
    # ────────────────────────────────────────────────────────────────────────────
    async def start_game(self, user: discord.User, channel: discord.TextChannel):
        if channel.id in GAMES:
            await safe_send(channel, "❌ Une partie est déjà en cours.")
            return

        game = Game(channel)
        game.add_player(user)
        game.deal()
        GAMES[channel.id] = game
        await send_hand(game.current_player(), game)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MilleBornes(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
