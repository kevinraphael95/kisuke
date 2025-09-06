# ────────────────────────────────────────────────────────────────────────────────
# 📌 bleach_duel.py — Mini-jeu interactif style Pokémon / Bleach
# Objectif : Duel interactif avec stats, types, moves personnalisés et ultimes
# Catégorie : Jeu
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select
import json
import os
import random

from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Fichier JSON des personnages
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_characters.json")

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Fonction pour charger le JSON
# ────────────────────────────────────────────────────────────────────────────────
def load_characters():
    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {DATA_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu du joueur pour choisir move
# ────────────────────────────────────────────────────────────────────────────────
class MoveSelectView(View):
    def __init__(self, bot, player, enemy):
        super().__init__(timeout=120)
        self.bot = bot
        self.player = player
        self.enemy = enemy
        self.message = None
        self.add_item(MoveSelect(self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)

class MoveSelect(Select):
    def __init__(self, parent_view: MoveSelectView):
        self.parent_view = parent_view
        options = []
        for move_name, move_data in parent_view.player["moves"].items():
            desc = f"Type: {move_data['type']}, Dégâts: {move_data.get('damage',0)}, Coût REI: {move_data.get('rei_cost',0)}"
            options.append(discord.SelectOption(label=move_name, description=desc))
        super().__init__(placeholder="Choisis ton move", options=options)

    async def callback(self, interaction: discord.Interaction):
        player = self.parent_view.player
        enemy = self.parent_view.enemy
        move_name = self.values[0]
        move = player["moves"][move_name]

        # IA choisit son move semi-stratégique
        enemy_move_name, enemy_move = self.choose_ai_move(enemy, player)

        # Calcul dégâts
        result_text = f"**{player['name']}** utilise {move_name}!\n**{enemy['name']}** utilise {enemy_move_name}!\n"

        def compute_damage(attacker, defender, mv):
            base = mv.get('damage',0) + attacker['stats'].get('REI',0)
            dmg = base - defender['stats'].get('TEC',0)
            return max(dmg,0)

        dmg_to_enemy = compute_damage(player, enemy, move)
        dmg_to_player = compute_damage(enemy, player, enemy_move)
        enemy['stats']['HP'] -= dmg_to_enemy
        player['stats']['HP'] -= dmg_to_player

        result_text += f"\n**Dégâts :** {enemy['name']} -{dmg_to_enemy}, {player['name']} -{dmg_to_player}"
        result_text += f"\n**HP :** {player['name']} {player['stats']['HP']} | {enemy['name']} {enemy['stats']['HP']}"

        # Vérifie fin combat
        if player['stats']['HP'] <=0 and enemy['stats']['HP']<=0:
            result_text += "\n⚔️ Égalité !"
            self.stop()
        elif player['stats']['HP'] <=0:
            result_text += f"\n💀 {player['name']} a perdu !"
            self.stop()
        elif enemy['stats']['HP'] <=0:
            result_text += f"\n🏆 {player['name']} a gagné !"
            self.stop()

        await safe_edit(interaction.message, content=result_text, view=self if self._running else None)

    def choose_ai_move(self, enemy, player):
        moves_list = list(enemy['moves'].items())
        ult = [m for m in moves_list if m[1].get('type')=='transform' and m[1].get('rei_cost',0)>=50]
        if enemy['stats']['HP']<50 and ult:
            return ult[0]
        return random.choice(moves_list)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class BleachDuel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _start_duel(self, channel: discord.abc.Messageable, player_name: str):
        characters = load_characters()
        if not characters:
            await safe_send(channel, "❌ Impossible de charger les personnages.")
            return

        # Menu sélection du perso joueur (exemple simple, prend le premier du dict)
        player_key = list(characters.keys())[0]  # Ici tu peux ajouter un vrai menu pour choisir
        player = characters[player_key]
        player['name'] = player_name

        # IA choisit perso aléatoire
        enemy_key = random.choice(list(characters.keys()))
        enemy = characters[enemy_key]
        enemy['name'] = enemy_key

        view = MoveSelectView(self.bot, player, enemy)
        view.message = await safe_send(channel, f"💥 Duel lancé ! {player['name']} contre {enemy['name']}", view=view)

    @app_commands.command(name="duel", description="Duel interactif style Pokémon / Bleach")
    @app_commands.checks.cooldown(1,10.0,key=lambda i:i.user.id)
    async def slash_duel(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._start_duel(interaction.channel, interaction.user.name)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /duel] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="duel")
    @commands.cooldown(1,10.0,commands.BucketType.user)
    async def prefix_duel(self, ctx: commands.Context):
        try:
            await self._start_duel(ctx.channel, ctx.author.name)
        except Exception as e:
            print(f"[ERREUR !duel] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = BleachDuel(bot)
    for command in cog.get_commands():
        if not hasattr(command,"category"):
            command.category = "Jeu"
    await bot.add_cog(cog)
