# ────────────────────────────────────────────────────────────────────────────────
# 📌 jardin_utils.py — Fonctions utilitaires pour le jardin
# Objectif : Contient la logique métier et la manipulation des jardins
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import json
import random
import datetime
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Chargement des constantes depuis un JSON
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

TABLE_NAME = "gardens"

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
async def get_or_create_garden(user_id: int, username: str) -> dict:
    """Récupère le jardin d'un utilisateur ou le crée s'il n'existe pas."""
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
        "last_fertilize": None,
        "potions": {}
    }
    supabase.table(TABLE_NAME).insert(new_garden).execute()
    return new_garden


def build_garden_embed(garden: dict, viewer_id: int):
    """Construit l'embed du jardin pour Discord."""
    import discord  # Import local pour éviter des conflits circulaires
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
    """Fait pousser aléatoirement des fleurs dans le jardin."""
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
    """Cueille toutes les fleurs du jardin et les ajoute à l'inventaire."""
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


def build_potions_embed(potions: dict):
    """Construit l'embed pour afficher les potions."""
    import discord
    if not potions:
        desc = "🧪 Tu n’as aucune potion."
    else:
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
