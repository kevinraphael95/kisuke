# ────────────────────────────────────────────────────────────────────────────────
# 📌 jardin_utils.py — Fonctions utilitaires pour le jardin
# ────────────────────────────────────────────────────────────────────────────────
import discord
import datetime
import random
from utils.supabase_client import supabase

# Ces constantes doivent être initialisées depuis le JSON dans jardin.py
TABLE_NAME = None
DEFAULT_GRID = None
DEFAULT_INVENTORY = None
FLEUR_EMOJIS = None
FLEUR_VALUES = None
FLEUR_SIGNS = None
FLEUR_LIST = None
FERTILIZE_COOLDOWN = None
FERTILIZE_PROBABILITY = None
POTIONS = None


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
