import datetime, random
from supabase import create_client, Client
import os, json
import discord

# ──────────────────────
# 🔌 Connexion Supabase
# ──────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "gardens"

# ──────────────────────
# 📦 Chargement config
# ──────────────────────
with open("data/potions.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

DEFAULT_GRID = CONFIG["default_grid"]
DEFAULT_INVENTORY = CONFIG["default_inventory"]
FLOWERS = CONFIG["flowers"]
FERTILIZE_CFG = CONFIG["fertilize"]
POTIONS = CONFIG["potions"]

FERTILIZE_COOLDOWN = datetime.timedelta(minutes=FERTILIZE_CFG["cooldown_minutes"])
FERTILIZE_PROBABILITY = FERTILIZE_CFG["probability"]

FLEUR_EMOJIS = {k: v["emoji"] for k, v in FLOWERS.items()}
FLEUR_VALUES = {k: v["value"] for k, v in FLOWERS.items()}
FLEUR_SIGNS = {k: v["sign"] for k, v in FLOWERS.items()}
FLEUR_LIST = list(FLEUR_EMOJIS.items())

# ──────────────────────
# 🧠 Fonctions utilitaires
# ──────────────────────
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
                h, m = divmod(int(remain.total_seconds()) // 60, 60)
                s = int(remain.total_seconds()) % 60
                cd_str = f"⏳ {h}h {m}m {s}s"
        except Exception:
            pass

    embed = discord.Embed(
        title=f"🏡 Jardin de {garden['username']}",
        description="\n".join(lines),
        color=discord.Color.green()
    )
    embed.add_field(
        name="Infos",
        value=f"Fleurs : {inv}\n"
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
