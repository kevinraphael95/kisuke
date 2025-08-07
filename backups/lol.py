# ────────────────────────────────────────────────────────────────────────────────
# 📌 league_of_legends_minijeu.py — Commande interactive !lol
# Objectif : Simuler une vraie partie de League of Legends en solo contre IA
# Catégorie : Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import random
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Constantes et données de base
# ────────────────────────────────────────────────────────────────────────────────
CHAMPIONS = [
    {"name": "Ahri", "role": "Mid", "emoji": "🦊", "hp": 100, "damage": 15},
    {"name": "Garen", "role": "Top", "emoji": "🛡️", "hp": 120, "damage": 12},
    {"name": "Jinx", "role": "Bot", "emoji": "💣", "hp": 90, "damage": 18},
    {"name": "Lee Sin", "role": "Jungle", "emoji": "🥋", "hp": 100, "damage": 14},
    {"name": "Lux", "role": "Mid", "emoji": "✨", "hp": 80, "damage": 20}
]

LANES = ["Top", "Mid", "Bot"]
ACTIONS = ["🔪 Last hit", "💥 Poke", "🛡️ Reculer", "📞 Appeler Jungler"]

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Vues de jeu — Phase de lane
# ────────────────────────────────────────────────────────────────────────────────
class LanePhaseView(View):
    def __init__(self, bot, player, enemy, ctx):
        super().__init__(timeout=60)
        self.bot = bot
        self.ctx = ctx
        self.player = player
        self.enemy = enemy
        self.cs = 0
        self.hp = player["hp"]
        self.enemy_hp = enemy["hp"]
        self.turn = 1
        for action in ACTIONS:
            self.add_item(LaneActionButton(label=action, view=self))

class LaneActionButton(Button):
    def __init__(self, label, view):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.custom_view = view

    async def callback(self, interaction: discord.Interaction):
        result = await self.resolve_action(self.label)
        embed = discord.Embed(
            title=f"{self.custom_view.player['emoji']} Phase de Lane - Tour {self.custom_view.turn}",
            description=result,
            color=discord.Color.blurple()
        )
        embed.add_field(name="Ton HP", value=f"{self.custom_view.hp}/100")
        embed.add_field(name="Ennemi HP", value=f"{self.custom_view.enemy_hp}/100")
        embed.add_field(name="CS", value=str(self.custom_view.cs))

        self.custom_view.turn += 1

        if self.custom_view.enemy_hp <= 0:
            embed.title = "🏆 Victoire en lane !"
            embed.description += "\nTu as dominé ta lane, bien joué."
            await safe_edit(interaction.message, embed=embed, view=None)
        elif self.custom_view.hp <= 0:
            embed.title = "💀 Défaite en lane"
            embed.description += "\nTu es mort en lane..."
            await safe_edit(interaction.message, embed=embed, view=None)
        else:
            await safe_edit(interaction.message, embed=embed, view=self.custom_view)

    async def resolve_action(self, action):
        dmg = self.custom_view.player["damage"]
        enemy_dmg = self.custom_view.enemy["damage"]

        if action == "🔪 Last hit":
            self.custom_view.cs += 1
            return "Tu as réussi un CS et gagné 15 golds."
        elif action == "💥 Poke":
            self.custom_view.enemy_hp -= dmg + random.randint(0, 5)
            self.custom_view.hp -= random.randint(0, 5)
            return "Tu as poké ton adversaire, mais il riposte légèrement."
        elif action == "🛡️ Reculer":
            heal = random.randint(5, 10)
            self.custom_view.hp = min(self.custom_view.player["hp"], self.custom_view.hp + heal)
            return f"Tu recules sous ta tour et récupères {heal} HP."
        elif action == "📞 Appeler Jungler":
            gank = random.random()
            if gank < 0.5:
                self.custom_view.enemy_hp -= dmg * 2
                return "Ton jungler est venu ! Vous avez mis l'adversaire très low."
            else:
                self.custom_view.hp -= enemy_dmg
                return "Ton jungler est occupé... tu prends des dégâts."

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class LeagueOfLegends(commands.Cog):
    """
    Commande !lol — Simule une partie de League of Legends contre l'IA
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="lol", help="Mini-jeu League of Legends solo.", description="Lance une partie LoL contre un bot.")
    async def lol(self, ctx: commands.Context):
        try:
            player = random.choice(CHAMPIONS)
            enemy = random.choice([c for c in CHAMPIONS if c != player and c["role"] == player["role"]])

            embed = discord.Embed(
                title="🏁 Début de la partie League of Legends !",
                description=f"Tu joues {player['emoji']} **{player['name']}** ({player['role']})\nAdversaire : {enemy['emoji']} **{enemy['name']}**",
                color=discord.Color.green()
            )
            embed.set_footer(text="Phase de lane en cours...")
            view = LanePhaseView(self.bot, player, enemy, ctx)
            await safe_send(ctx, embed=embed, view=view)

        except Exception as e:
            print(f"[ERREUR lol] {e}")
            await safe_send(ctx, "❌ Une erreur est survenue pendant la partie.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = LeagueOfLegends(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
