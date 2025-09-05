# ────────────────────────────────────────────────────────────────────────────────
# 📌 1000bornes.py — Jeu de 1000 Bornes Discord
# Objectif : Jouer à 1000 Bornes solo ou contre un bot
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 3 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
from discord.ui import View, Select
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
    def __init__(self, user: discord.User, is_bot: bool = False):
        self.user = user
        self.is_bot = is_bot
        self.hand: List[str] = []
        self.km = 0
        self.stopped = True
        self.completed = False

class Game:
    def __init__(self, channel: discord.TextChannel):
        self.channel = channel
        self.players: List[Player] = []
        self.deck: List[str] = self.build_deck()
        self.discard: List[str] = []
        self.current = 0

    def build_deck(self) -> List[str]:
        deck = []
        for card, count in DECK_COUNTS.items():
            deck.extend([card]*count)
        random.shuffle(deck)
        return deck

    def add_player(self, user: discord.User, is_bot: bool = False):
        self.players.append(Player(user, is_bot))

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
        self.current = (self.current + 1) % len(self.players)
        return self.players[self.current]

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI simplifiée
# ────────────────────────────────────────────────────────────────────────────────
class PlaySelect(Select):
    def __init__(self, game: Game, player: Player):
        self.game = game
        self.player = player
        options = [discord.SelectOption(label=f"{c} ({CARDS[c].get('name', c)})", value=c) for c in player.hand]
        super().__init__(placeholder="Choisis une carte", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.player.user.id:
            await interaction.response.send_message("Ce n'est pas ton tour", ephemeral=True)
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
        await interaction.response.send_message(f"{self.player.user.mention} a joué {card}")
        self.game.next_player()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
GAMES = {}

class MilleBornes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="1000")
    async def start_command(self, ctx: commands.Context):
        if ctx.channel.id in GAMES:
            await ctx.send("Une partie est déjà en cours.")
            return
        game = Game(ctx.channel)
        game.add_player(ctx.author)
        game.deal()
        GAMES[ctx.channel.id] = game
        await ctx.send("Partie de 1000 Bornes commencée !")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MilleBornes(bot))
