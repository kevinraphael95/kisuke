# ────────────────────────────────────────────────────────────────────────────────
# 📌 combat.py — Commande interactive /combat et !combat
# Objectif : Combat style Pokémon complet avec statuts et formes évolutives
# Catégorie : Bleach
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import random, os, json
from utils.discord_utils import safe_send

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Gestion des personnages et combat
# ────────────────────────────────────────────────────────────────────────────────
CHAR_DIR = os.path.join("data", "personnages")
COMBAT_FILE = os.path.join("data", "combat.json")

with open(COMBAT_FILE, "r", encoding="utf-8") as f:
    COMBAT_DATA = json.load(f)

TYPE_EFF = COMBAT_DATA["type_effectiveness"]
TYPE_EMOJI = COMBAT_DATA["types_emoji"]
CATEGORIE_EMOJI = COMBAT_DATA["categories_emoji"]
STATUTS = COMBAT_DATA["statuts"]
BOOSTS = COMBAT_DATA["boosts"]

def load_character(name: str):
    path = os.path.join(CHAR_DIR, f"{name.lower()}.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        char = json.load(f)
        char["image"] = char.get("images", [""])[0] if char.get("images") else ""
        return char

def list_characters():
    return [f.replace(".json", "") for f in os.listdir(CHAR_DIR) if f.endswith(".json")]

def multiplier_type(atk_type, cible_type):
    return TYPE_EFF.get(atk_type, {}).get(cible_type, 1)

def init_combat(p: dict):
    p = p.copy()
    p["pv"] = p["stats_base"]["total_stats"] // 3  # Exemple PV calculé depuis stats_total
    p["boosts"] = {b: 0 for b in BOOSTS}
    p["statut"] = None
    p["forme_actuelle"] = "Normal"
    p["sleep_turns"] = 0
    for f in p["formes"].values():
        for a in f["attaques"]:
            a["PP"] = a.get("PP", 10)
    return p

def attaque_disponible(p: dict):
    return [a for a in p["formes"][p["forme_actuelle"]]["attaques"] if a["PP"] > 0]

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Gestion des statuts
# ────────────────────────────────────────────────────────────────────────────────
def appliquer_statut(p: dict, narratif: list):
    if not p["statut"]:
        return False
    s = STATUTS[p["statut"]]
    if p["statut"] == "Paralysie":
        if random.random() < s["chance_move"]:
            narratif.append(f"{s['emoji']} **{p['nom']}** est paralysé et rate son tour !")
            return True
    elif p["statut"] == "Sommeil":
        if p["sleep_turns"] == 0:
            p["sleep_turns"] = random.randint(1, s["tour_max"])
        if p["sleep_turns"] > 0:
            p["sleep_turns"] -= 1
            narratif.append(f"{s['emoji']} **{p['nom']}** dort et ne peut agir !")
            return True
    elif p["statut"] == "Gel":
        if random.random() < s["chance_move"]:
            narratif.append(f"{s['emoji']} **{p['nom']}** est gelé et rate son tour !")
            return True
    elif p["statut"] == "Confusion":
        if random.random() < s["chance_self"]:
            deg = s["degats"]
            p["pv"] -= deg
            narratif.append(f"{s['emoji']} **{p['nom']}** est confus et se blesse ({deg} PV) !")
            return True
    elif p["statut"] == "Poison":
        deg = s["degats"]
        p["pv"] -= deg
        narratif.append(f"{s['emoji']} **{p['nom']}** subit {deg} PV de dégâts de poison !")
    elif p["statut"] == "Brûlure":
        deg = s["degats"]
        atk_mod = s["attaque_mod"]
        p["pv"] -= deg
        p["boosts"]["Attaque"] *= atk_mod
        narratif.append(f"{s['emoji']} **{p['nom']}** subit {deg} PV de brûlure et attaque réduite !")
    return False

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Calcul et application des dégâts
# ────────────────────────────────────────────────────────────────────────────────
def calcul_degats(a, d, atk):
    if atk["categorie"] == "Offensive":
        atk_stat = a["stats_base"]["attaque"] * (1 + a["boosts"]["Attaque"] / 2)
        def_stat = d["stats_base"]["defense"] * (1 + d["boosts"]["Defense"] / 2)
    else:
        return 0, 1, False
    base = ((2 * 50 / 5 + 2) * atk["puissance"] * (atk_stat / def_stat)) / 50 + 2
    mult = multiplier_type(atk["type"], d["type"])
    rand = random.uniform(0.85, 1)
    crit = 1.5 if random.random() < 0.0625 else 1
    return int(base * mult * rand * crit), mult, crit > 1

def appliquer_attaque(a, d, atk, narratif):
    if atk["categorie"] == "Soin":
        soin = atk["puissance"]
        a["pv"] = min(a["stats_base"]["total_stats"] // 3, a["pv"] + soin)
        narratif.append(f"{CATEGORIE_EMOJI['Soin']} **{a['nom']}** utilise *{atk['nom']}* et se soigne {soin} PV !")
        return
    degats, mult, crit = calcul_degats(a, d, atk)
    d["pv"] -= degats
    emoji_type = TYPE_EMOJI.get(atk["type"], "")
    txt = f"{CATEGORIE_EMOJI['Offensive']} **{a['nom']}** utilise *{atk['nom']}* {emoji_type} et inflige {degats} PV à **{d['nom']}** !"
    if crit: txt += " ⚡ Coup critique !"
    if mult > 1: txt += " 💥 Super efficace !"
    elif mult < 1: txt += " ⚠️ Pas très efficace..."
    narratif.append(txt)
    if "statut" in atk: d["statut"] = atk["statut"]

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Forme suivante (évolution en combat)
# ────────────────────────────────────────────────────────────────────────────────
def forme_suivante(p: dict):
    formes = list(p["formes"].keys())
    idx = formes.index(p["forme_actuelle"])
    if idx < len(formes) - 1 and random.random() < 0.15:
        p["forme_actuelle"] = formes[idx + 1]
        return f"✨ **{p['nom']}** passe en **{p['forme_actuelle']}** !"
    return None

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CombatCommand(commands.Cog):
    """Commande /combat et !combat — Combat Pokémon complet avec statuts et formes évolutives"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="combat",
        description="⚔️ Combat style Pokémon entre 2 persos."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_combat(self, interaction: discord.Interaction):
        await self.run_combat(interaction.channel)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="combat")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_combat(self, ctx: commands.Context):
        await self.run_combat(ctx.channel)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔧 Fonction principale du combat
    # ────────────────────────────────────────────────────────────────────────────
    async def run_combat(self, channel):
        try:
            persos = [load_character(n) for n in list_characters()]
            persos = [p for p in persos if p]
            if len(persos) < 2:
                return await safe_send(channel, "❌ Pas assez de personnages.")
            p1, p2 = random.sample(persos, 2)
            p1, p2 = init_combat(p1), init_combat(p2)
            narratif = [f"⚔️ **Combat : {p1['nom']} vs {p2['nom']}** ⚔️\n"]

            tour = 0
            while p1["pv"] > 0 and p2["pv"] > 0 and tour < 50:
                tour += 1
                narratif.append(f"\n🔁 **Tour {tour}**")
                tour_order = sorted([p1, p2], key=lambda x: x["stats_base"]["rapidite"] + random.randint(0, 10), reverse=True)
                for attaquant in tour_order:
                    defenseur = p2 if attaquant == p1 else p1
                    if attaquant["pv"] <= 0 or defenseur["pv"] <= 0:
                        continue
                    if appliquer_statut(attaquant, narratif):
                        continue
                    dispo = attaque_disponible(attaquant)
                    if not dispo:
                        atk = {"nom": "Tacle", "type": "Normal", "categorie": "Offensive", "puissance": 40, "PP": 1}
                    else:
                        atk = random.choice(dispo)
                        atk["PP"] -= 1
                    appliquer_attaque(attaquant, defenseur, atk, narratif)
                    fs = forme_suivante(attaquant)
                    if fs:
                        narratif.append(fs)
                    if defenseur["pv"] <= 0:
                        narratif.append(f"\n🏆 **{attaquant['nom']}** remporte le combat !")
                        break
                else:
                    continue
                break

            # Embed final
            embed = discord.Embed(title=f"🗡️ {p1['nom']} vs {p2['nom']}", description="\n".join(narratif), color=discord.Color.red())
            embed.set_thumbnail(url=p1["image"])
            embed.set_image(url=p2["image"])
            await safe_send(channel, embed=embed)

        except Exception as e:
            import traceback; traceback.print_exc()
            await safe_send(channel, f"❌ Erreur dans !combat : `{e}`")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CombatCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
