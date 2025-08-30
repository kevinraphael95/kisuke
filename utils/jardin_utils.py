# ────────────────────────────────────────────────────────────────────────────────
# 📌 jardin_utils.py — Fonctions utilitaires pour le jardin
# ────────────────────────────────────────────────────────────────────────────────
import discord
import datetime
import os
from supabase import create_client
import json
import random

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Connexion Supabase
# ────────────────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Chargement des constantes depuis JSON
# ────────────────────────────────────────────────────────────────────────────────
with open("data/jardin.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

DEFAULT_GRID = DATA["DEFAULT_GRID"]
DEFAULT_INVENTORY = DATA["DEFAULT_INVENTORY"]
FLEUR_EMOJIS = DATA["FLEUR_EMOJIS"]
FLEUR_LIST = list(FLEUR_EMOJIS.items())
FLEUR_VALUES = DATA["FLEUR_VALUES"]
FLEUR_SIGNS = DATA["FLEUR_SIGNS"]
POTIONS = DATA["POTIONS"]
TABLE_NAME = DATA.get("TABLE_NAME", "gardens")
FERTILIZE_PROBABILITY = DATA["FERTILIZE_PROBABILITY"]
FERTILIZE_COOLDOWN = datetime.timedelta(seconds=DATA["FERTILIZE_COOLDOWN"])

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
async def get_or_create_garden(user_id: int, username: str):
    """Récupère le jardin d’un utilisateur ou le crée si inexistant."""
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
    """Construit l’embed représentant le jardin."""
    lines = garden["garden_grid"]
    inv = " / ".join(f"{FLEUR_EMOJIS[f]}{garden['inventory'].get(f, 0)}" for f in FLEUR_EMOJIS)

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
    """Fait pousser de nouvelles fleurs sur le jardin."""
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
    """Coupe les fleurs et met à jour l’inventaire."""
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
