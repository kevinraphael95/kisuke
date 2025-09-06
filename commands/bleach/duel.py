# ────────────────────────────────────────────────────────────────────────────────
# 📌 bleach_pkmn_duel.py — Mini-jeu interactif style Pokémon / Bleach
# Objectif : Duel interactif avec stats, types, attaques personnalisées et ultimes
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
DATA_JSON_PATH = os.path.join("data", "combat.json")

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
# 🔹 Modificateur de type
# ────────────────────────────────────────────────────────────────────────────────
TYPE_CHART = {
    "Shinigami": {"strong": ["Quincy"], "weak": ["Arrancar"]},
    "Hollow": {"strong": ["Shinigami"], "weak": ["Quincy"]},
    "Quincy": {"strong": ["Hollow"], "weak": ["Shinigami"]},
    "Arrancar": {"strong": ["Shinigami"], "weak": ["Quincy"]}
}

def type_modifier(attack_type, target_type):
    if target_type in TYPE_CHART.get(attack_type, {}).get("strong", []):
        return 1.5
    elif target_type in TYPE_CHART.get(attack_type, {}).get("weak", []):
        return 0.5
    return 1.0

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu du joueur pour choisir attaque
# ────────────────────────────────────────────────────────────────────────────────
class AttackSelectView(View):
    def __init__(self, bot, player, enemy):
        super().__init__(timeout=120)
        self.bot = bot
        self.player = player
        self.enemy = enemy
        self.message = None
        self.add_item(AttackSelect(self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)

class AttackSelect(Select):
    def __init__(self, parent_view: AttackSelectView):
        self.parent_view = parent_view
        options = []
        for atk_name, atk_data in parent_view.player["attacks"].items():
            desc = f"Type: {atk_data['type']}, Power: {atk_data['power']}"
            if atk_data.get('cooldown'):
                desc += f", Cooldown: {atk_data['cooldown']}"
            options.append(discord.SelectOption(label=atk_name, description=desc))
        super().__init__(placeholder="Choisis ton attaque", options=options)

    async def callback(self, interaction: discord.Interaction):
        player = self.parent_view.player
        enemy = self.parent_view.enemy
        attack_name = self.values[0]
        attack = player["attacks"][attack_name]

        # IA choisit son attaque semi-stratégique
        enemy_attack_name, enemy_attack = self.choose_ai_attack(enemy, player)

        # Calcul des dégâts
        result_text = f"**{player['name']}** utilise {attack_name} !\n**{enemy['name']}** utilise {enemy_attack_name} !\n"

        def compute_damage(attacker, defender, atk):
            base = atk['power'] + attacker['stats'].get('SP_ATK', 0)
            mod = type_modifier(atk['type'], defender['type'])
            dmg = int(base * mod) - defender['stats'].get('SP_DEF', 0)
            return max(dmg, 0)

        dmg_to_enemy = compute_damage(player, enemy, attack)
        dmg_to_player = compute_damage(enemy, player, enemy_attack)
        enemy['hp'] -= dmg_to_enemy
        player['hp'] -= dmg_to_player

        result_text += f"\n**Dégâts :** {enemy['name']} -{dmg_to_enemy}, {player['name']} -{dmg_to_player}"
        result_text += f"\n**HP :** {player['name']} {player['hp']} | {enemy['name']} {enemy['hp']}"

        # Vérifie fin de combat
        if player['hp'] <= 0 and enemy['hp'] <= 0:
            result_text += "\n⚔️ Égalité !"
            self.stop()
        elif player['hp'] <= 0:
            result_text += f"\n💀 {player['name']} a perdu !"
            self.stop()
        elif enemy['hp'] <= 0:
            result_text += f"\n🏆 {player['name']} a gagné !"
            self.stop()

        await safe_edit(interaction.message, content=result_text, view=self if self._running else None)

    def choose_ai_attack(self, enemy, player):
        available_attacks = list(enemy['attacks'].items())
        # Ultime si HP < 50%
        ult = [a for a in available_attacks if a[1].get('cooldown')]
        if enemy['hp'] < 50 and ult:
            return ult[0]
        # Sinon attaque standard
        return random.choice(available_attacks)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class BleachPkmnDuel(commands.Cog):
    """Mini-jeu interactif style Pokémon / Bleach"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _start_duel(self, channel: discord.abc.Messageable, player_name: str):
        characters = load_characters()
        if not characters:
            await safe_send(channel, "❌ Impossible de charger les personnages.")
            return
        # Choix aléatoire IA
        enemy = random.choice(list(characters.values()))
        # Joueur Ichigo par défaut (ou tu peux ajouter menu de choix)
        player = characters['Ichigo']
        player['name'] = player_name
        view = AttackSelectView(self.bot, player, enemy)
        view.message = await safe_send(channel, f"💥 Duel lancé ! {player['name']} contre {enemy['name']}", view=view)

    @app_commands.command(name="duel", description="Duel style Pokémon / Bleach")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def slash_bleach_pkmn_duel(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._start_duel(interaction.channel, interaction.user.name)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /bleach_pkmn_duel] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="duel")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_bleach_pkmn_duel(self, ctx: commands.Context):
        try:
            await self._start_duel(ctx.channel, ctx.author.name)
        except Exception as e:
            print(f"[ERREUR !bleach_pkmn_duel] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = BleachPkmnDuel(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
