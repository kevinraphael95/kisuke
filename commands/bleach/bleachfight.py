# ────────────────────────────────────────────────────────────────────────────────
# 📌 bleachfight.py — Combat solo Bleach /bleachfight et !bleachfight
# Objectif : Jeu de combat solo contre le bot, choix de perso, attaques, transformations
# Catégorie : Bleach
# Accès : Tous
# Cooldown : 1 combat / 30 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button
import json
import os
import random

from utils.discord_utils import safe_send, safe_edit, safe_respond

CHAR_JSON_PATH = os.path.join("data", "bleach_characters.json")

def load_characters():
    try:
        with open(CHAR_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Sélection du personnage
# ────────────────────────────────────────────────────────────────────────────────
class CharacterSelectView(View):
    def __init__(self, bot, characters, player_data):
        super().__init__(timeout=60)
        self.bot = bot
        self.characters = characters
        self.player_data = player_data
        self.message = None
        self.add_item(CharacterSelect(self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)

class CharacterSelect(Select):
    def __init__(self, parent_view: CharacterSelectView):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=char) for char in self.parent_view.characters.keys()]
        super().__init__(placeholder="Choisis ton personnage", options=options)

    async def callback(self, interaction: discord.Interaction):
        char_name = self.values[0]
        self.parent_view.player_data["player"] = {
            "name": char_name,
            "stats": self.parent_view.characters[char_name]["stats"].copy(),
            "moves": self.parent_view.characters[char_name]["moves"]
        }

        # Choix aléatoire du bot
        bot_char = random.choice(list(self.parent_view.characters.keys()))
        self.parent_view.player_data["bot"] = {
            "name": bot_char,
            "stats": self.parent_view.characters[bot_char]["stats"].copy(),
            "moves": self.parent_view.characters[bot_char]["moves"]
        }

        await safe_respond(interaction, f"✅ Tu as choisi **{char_name}** ! Le bot joue **{bot_char}**.", ephemeral=True)
        # Lancer le combat en DM
        try:
            dm = await interaction.user.create_dm()
            await safe_send(dm, "⚔️ Le combat commence !")
            await interaction.message.delete()
            await start_fight(interaction.user, self.parent_view.player_data)
        except Exception as e:
            print(f"[ERREUR DM] {e}")
            await safe_respond(interaction, "❌ Impossible de créer le DM pour le combat.", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Menu combat (boutons)
# ────────────────────────────────────────────────────────────────────────────────
class FightMenu(View):
    def __init__(self, user, player, bot_char):
        super().__init__(timeout=120)
        self.user = user
        self.player = player
        self.bot_char = bot_char
        self.message = None

        for move_name in player["moves"].keys():
            self.add_item(FightButton(move_name, self))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)

class FightButton(Button):
    def __init__(self, move_name, parent_view: FightMenu):
        super().__init__(label=move_name, style=discord.ButtonStyle.primary)
        self.parent_view = parent_view
        self.move_name = move_name

    async def callback(self, interaction: discord.Interaction):
        player = self.parent_view.player
        bot_char = self.parent_view.bot_char
        move = player["moves"][self.move_name]

        # Vérifier REI
        if move.get("rei_cost", 0) > player["stats"]["REI"]:
            await safe_respond(interaction, f"❌ Pas assez de Reiatsu pour **{self.move_name}** !", ephemeral=True)
            return

        # Joueur attaque
        player["stats"]["REI"] -= move.get("rei_cost", 0)
        dmg = move.get("damage", 0)
        bot_char["stats"]["HP"] -= dmg
        result = f"💥 **{player['name']}** utilise **{self.move_name}** et inflige {dmg} dégâts !\n"
        result += f"🎯 **{bot_char['name']}** a {bot_char['stats']['HP']} HP restants.\n"

        # Vérifier victoire
        if bot_char["stats"]["HP"] <= 0:
            result += f"🏆 Tu as vaincu **{bot_char['name']}** !"
            await safe_edit(interaction.message, content=result, view=None)
            return

        # Bot attaque aléatoire
        bot_move_name = random.choice(list(bot_char["moves"].keys()))
        bot_move = bot_char["moves"][bot_move_name]
        dmg_bot = bot_move.get("damage", 0)
        player["stats"]["HP"] -= dmg_bot
        result += f"🤖 **{bot_char['name']}** utilise **{bot_move_name}** et inflige {dmg_bot} dégâts !\n"
        result += f"🎯 **{player['name']}** a {player['stats']['HP']} HP restants."

        # Vérifier défaite
        if player["stats"]["HP"] <= 0:
            result += f"\n💀 Tu as été vaincu par **{bot_char['name']}**."

        # Actualiser le menu
        await safe_edit(interaction.message, content=result, view=self.parent_view)

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Fonction combat solo
# ────────────────────────────────────────────────────────────────────────────────
async def start_fight(user, player_data):
    dm = await user.create_dm()
    view = FightMenu(user, player_data["player"], player_data["bot"])
    view.message = await safe_send(dm, "⚔️ À toi de jouer ! Choisis ton action :", view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class BleachFight(commands.Cog):
    """
    Commande /bleachfight et !bleachfight — Combat solo contre le bot
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="bleachfight",
        description="Choisis ton personnage et combats le bot en DM !"
    )
    @app_commands.checks.cooldown(1, 30.0, key=lambda i: (i.user.id))
    async def slash_bleachfight(self, interaction: discord.Interaction):
        try:
            characters = load_characters()
            if not characters:
                await safe_respond(interaction, "❌ Impossible de charger les personnages.", ephemeral=True)
                return
            player_data = {}
            view = CharacterSelectView(self.bot, characters, player_data)
            view.message = await safe_respond(interaction, "🎮 Choisis ton personnage :", view=view, ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /bleachfight] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="bleachfight")
    @commands.cooldown(1, 30.0, commands.BucketType.user)
    async def prefix_bleachfight(self, ctx: commands.Context):
        try:
            characters = load_characters()
            if not characters:
                await safe_send(ctx.channel, "❌ Impossible de charger les personnages.")
                return
            player_data = {}
            view = CharacterSelectView(self.bot, characters, player_data)
            view.message = await safe_send(ctx.author, "🎮 Choisis ton personnage :", view=view)
        except Exception as e:
            print(f"[ERREUR !bleachfight] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = BleachFight(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
