# ────────────────────────────────────────────────────────────────────────────────
# 📌 jardin.py — Commande interactive /jardin et !jardin
# Objectif : Chaque utilisateur a un jardin persistant avec des fleurs
# Catégorie : Jeu
# Accès : Tout le monde
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import os
import random
import datetime
import json
import discord
from discord import app_commands
from discord.ext import commands
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 table name
# ────────────────────────────────────────────────────────────────────────────────
TABLE_NAME = "gardens"

# ────────────────────────────────────────────────────────────────────────────────
# 🌱 Chargement des constantes depuis un JSON
# ────────────────────────────────────────────────────────────────────────────────
with open("data/jardin_config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

DEFAULT_GRID = CONFIG["DEFAULT_GRID"]
DEFAULT_INVENTORY = CONFIG["DEFAULT_INVENTORY"]

FLEUR_EMOJIS = CONFIG["FLEUR_EMOJIS"]
FLEUR_VALUES = CONFIG["FLEUR_VALUES"]
FLEUR_SIGNS = CONFIG["FLEUR_SIGNS"]

FLEUR_LIST = list(FLEUR_EMOJIS.items())

FERTILIZE_COOLDOWN = datetime.timedelta(minutes=CONFIG["FERTILIZE_COOLDOWN_MINUTES"])
FERTILIZE_PROBABILITY = CONFIG["FERTILIZE_PROBABILITY"]

POTIONS = CONFIG["POTIONS"]


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
async def get_or_create_garden(user_id: int, username: str):
    res = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).execute()
    if res.data:
        return res.data[0]

    new_garden = {
        "user_id": user_id,
        "username": username,
        "garden_grid": DEFAULT_GRID.copy(),
        "inventory": DEFAULT_INVENTORY.copy(),
        "argent": 0,
        "armee": "",
        "last_fertilize": None
    }
    supabase.table(TABLE_NAME).insert(new_garden).execute()
    return new_garden


def build_garden_embed(garden: dict, viewer_id: int) -> discord.Embed:
    lines = garden["garden_grid"]
    inv_dict = garden["inventory"]
    inv = " / ".join(f"{FLEUR_EMOJIS[f]}{inv_dict.get(f, 0)}" for f in FLEUR_EMOJIS)

    cd_str = "✅ Disponible"
    if garden.get("last_fertilize"):
        try:
            last_dt = datetime.datetime.fromisoformat(garden["last_fertilize"])
            now = datetime.datetime.now(datetime.timezone.utc)
            remain = last_dt + FERTILIZE_COOLDOWN - now
            if remain.total_seconds() > 0:
                total_seconds = int(remain.total_seconds())
                minutes, seconds = divmod(total_seconds, 60)
                hours, minutes = divmod(minutes, 60)
                cd_str = f"⏳ {hours}h {minutes}m {seconds}s"
        except Exception as e:
            print(f"[ERREUR parse last_fertilize] {e}")

    embed = discord.Embed(
        title=f"🏡 Jardin de {garden['username']}",
        description="\n".join(lines),
        color=discord.Color.green()
    )
    embed.add_field(
        name="Infos",
        value=f"Fleurs possédées : {inv}\n"
              f"Armée : {garden['armee'] or '—'} | Argent : {garden['argent']}💰\n"
              f"Cooldown engrais : {cd_str}",
        inline=False
    )
    return embed

def pousser_fleurs(lines: list[str]) -> list[str]:
    new_lines = []
    for line in lines:
        chars = []
        for c in line:
            if c == "🌱" and random.random() < FERTILIZE_PROBABILITY:
                _, emoji = random.choice(FLEUR_LIST)
                chars.append(emoji)
            else:
                chars.append(c)
        new_lines.append("".join(chars))
    return new_lines

def couper_fleurs(lines: list[str], garden: dict) -> tuple[list[str], dict]:
    new_lines = []
    inv = garden["inventory"]
    for line in lines:
        chars = []
        for c in line:
            for col, emoji in FLEUR_EMOJIS.items():
                if c == emoji:
                    inv[col] = inv.get(col, 0) + 1
                    c = "🌱"
            chars.append(c)
        new_lines.append("".join(chars))
    garden["inventory"] = inv
    return new_lines, garden

def build_potions_embed(potions: dict) -> discord.Embed:
    if not potions:
        desc = "🧪 Tu n’as aucune potion."
    else:
        # Tri par valeur croissante
        sorted_potions = dict(sorted(
            potions.items(),
            key=lambda x: next((int(v) for v, n in POTIONS.items() if n == x[0]), 0)
        ))
        desc = "\n".join(f"{name} x{qty}" for name, qty in sorted_potions.items())

    embed = discord.Embed(
        title="🧪 Tes potions",
        description=desc,
        color=discord.Color.teal()
    )
    return embed


# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Alchimie interactive
# ────────────────────────────────────────────────────────────────────────────────
# (inchangé, identique à ta version précédente)
# … code AlchimieView ici …
# ────────────────────────────────────────────────────────────────────────────────


# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Jardin interactif (boutons par fleur)
# ────────────────────────────────────────────────────────────────────────────────
class JardinInteractifView(discord.ui.View):
    def __init__(self, garden: dict, user_id: int, timeout=180):
        super().__init__(timeout=timeout)
        self.garden = garden
        self.user_id = user_id
        self.build_buttons()

    def build_buttons(self):
        self.clear_items()
        for row_idx, line in enumerate(self.garden["garden_grid"]):
            for col_idx, char in enumerate(line):
                button = discord.ui.Button(label=char, style=discord.ButtonStyle.green, row=row_idx)
                button.callback = self.make_callback(row_idx, col_idx, char)
                self.add_item(button)
        # Ajouter boutons supplémentaires (engrais, couper, alchimie, potions)
        self.add_item(discord.ui.Button(label="Engrais", emoji="💩", style=discord.ButtonStyle.green))
        self.add_item(discord.ui.Button(label="Couper", emoji="✂️", style=discord.ButtonStyle.secondary))
        self.add_item(discord.ui.Button(label="Alchimie", emoji="⚗️", style=discord.ButtonStyle.blurple))
        self.add_item(discord.ui.Button(label="Potions", emoji="🧪", style=discord.ButtonStyle.green))

    def make_callback(self, row, col, char):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

            if char in FLEUR_EMOJIS.values():
                # Cueille la fleur
                for name, emoji in FLEUR_EMOJIS.items():
                    if emoji == char:
                        self.garden["inventory"][name] = self.garden["inventory"].get(name, 0) + 1
                self.garden["garden_grid"][row] = self.garden["garden_grid"][row][:col] + "🌱" + self.garden["garden_grid"][row][col+1:]
                await self.update_message(interaction)
            else:
                await interaction.response.send_message("❌ Rien à cueillir ici !", ephemeral=True)
        return callback

    async def update_message(self, interaction):
        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=self)


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Jardin(commands.Cog):
    """Commande /jardin et !jardin — Voir son jardin"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_garden(self, target_user, viewer_id, respond_func):
        try:
            garden = await get_or_create_garden(target_user.id, target_user.name)
            embed = build_garden_embed(garden, viewer_id)
            view = None
            if target_user.id == viewer_id:
                view = JardinInteractifView(garden, viewer_id)
            await respond_func(embed=embed, view=view)
        except Exception as e:
            print(f"[ERREUR jardin] {e}")
            await respond_func("❌ Une erreur est survenue.", ephemeral=True)


    # ───────── Commande Slash ─────────
    @app_commands.command(name="jardin", description="Affiche ton jardin ou celui d'un autre utilisateur 🌱")
    @app_commands.checks.cooldown(1, 5.0)
    async def slash_jardin(self, interaction:discord.Interaction, user:discord.User=None):
        target = user or interaction.user
        await self._send_garden(target, interaction.user.id, lambda **kwargs: safe_respond(interaction, **kwargs))

    # ───────── Commande Préfixe ─────────
    @commands.command(name="jardin")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def prefix_jardin(self, ctx:commands.Context, user:discord.User=None):
        target = user or ctx.author
        await self._send_garden(target, ctx.author.id, lambda **kwargs: safe_send(ctx.channel, **kwargs))


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Jardin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeu"
    await bot.add_cog(cog)
