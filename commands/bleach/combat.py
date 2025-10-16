# ────────────────────────────────────────────────────────────────────────────────
# 📌 combat.py — Commande interactive !combat
# Objectif : Simule un combat immersif entre 2 personnages de Bleach avec stats, endurance et effets.
# Catégorie : Bleach
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import random
import os
import json
from utils.discord_utils import safe_send

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Gestion des personnages
# ────────────────────────────────────────────────────────────────────────────────
CHAR_DIR = os.path.join("data", "personnages")

def load_character(name: str):
    path = os.path.join(CHAR_DIR, f"{name.lower()}.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        char = json.load(f)
        char["image"] = char.get("images", [""])[0] if char.get("images") else ""
        return char

def list_characters():
    files = os.listdir(CHAR_DIR)
    return [f.replace(".json", "") for f in files if f.endswith(".json")]

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Fonctions utilitaires du combat
# ────────────────────────────────────────────────────────────────────────────────
def init_combat(p: dict):
    """Initialise un personnage pour le combat."""
    p = p.copy()
    p["pv"] = 100
    p["endurance"] = 100
    p["forme_actuelle"] = "Normal"
    return p

def attaque_disponible(p: dict):
    """Retourne la liste des attaques que le perso peut utiliser selon l'endurance."""
    forme = p["formes"][p["forme_actuelle"]]
    attaques = []
    for a in forme["attaques"]:
        if a.get("cout_endurance", 0) <= p["endurance"]:
            attaques.append(a)
    return attaques

def attaque_faible(p: dict):
    """Retourne une attaque faible si endurance à 0."""
    return {"nom": "Attaque faible", "puissance": 10, "cout_endurance": 0}

def appliquer_degats(cible: dict, degats: int, narratif: list, attaquant_nom: str, attaque_nom: str):
    cible["pv"] -= degats
    narratif.append(f"💥 **{attaquant_nom}** utilise *{attaque_nom}* et inflige **{degats} PV** à **{cible['nom']}** ! (PV restants : {cible['pv']})")
    return narratif

def forme_suivante(p: dict):
    """Chance de passer à la forme suivante si possible."""
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
    """Commande !combat — Combat immersif entre 2 personnages de Bleach."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="combat",
        help="⚔️ Simule un combat immersif entre 2 personnages de Bleach."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def combat(self, ctx: commands.Context):
        try:
            persos = [load_character(n) for n in list_characters()]
            persos = [p for p in persos if p is not None]

            if len(persos) < 2:
                return await safe_send(ctx.channel, "❌ Pas assez de personnages pour le combat.")

            p1, p2 = random.sample(persos, 2)
            p1, p2 = init_combat(p1), init_combat(p2)

            narratif = [f"⚔️ **Combat : {p1['nom']} vs {p2['nom']}** ⚔️\n"]

            tour_order = sorted([p1, p2], key=lambda x: x["stats_base"]["rapidite"] + random.randint(0, 10), reverse=True)

            tour = 0
            while p1["pv"] > 0 and p2["pv"] > 0 and tour < 30:
                tour += 1
                narratif.append(f"\n🔁 **Tour {tour}**")

                for attaquant in tour_order:
                    defenseur = p2 if attaquant == p1 else p1
                    if attaquant["pv"] <= 0 or defenseur["pv"] <= 0:
                        continue

                    dispo = attaque_disponible(attaquant)
                    attaque = random.choice(dispo) if dispo else attaque_faible(attaquant)
                    degats = max(5, attaque["puissance"] + attaquant["stats_base"]["attaque"] - defenseur["stats_base"]["defense"])
                    narratif = appliquer_degats(defenseur, degats, narratif, attaquant["nom"], attaque["nom"])
                    attaquant["endurance"] -= attaque.get("cout_endurance", 0)

                    # Vérification forme suivante
                    fs = forme_suivante(attaquant)
                    if fs:
                        narratif.append(fs)

                    if defenseur["pv"] <= 0:
                        narratif.append(f"\n🏆 **{attaquant['nom']}** remporte le combat !")
                        break

            # Si le combat dure trop longtemps
            if tour >= 30 and p1["pv"] > 0 and p2["pv"] > 0:
                narratif.append("\n⏱️ Le combat s'achève par épuisement mutuel !")

            # Si les deux sont encore debout à la fin
            if p1["pv"] > 0 and p2["pv"] > 0:
                gagnant = p1 if p1["pv"] > p2["pv"] else p2
                narratif.append(f"\n🏁 Fin du combat, vainqueur : **{gagnant['nom']}**")

            # Création embed
            embed = discord.Embed(
                title=f"🗡️ {p1['nom']} vs {p2['nom']}",
                description="\n".join(narratif),
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=p1["image"])
            embed.set_image(url=p2["image"])
            await safe_send(ctx.channel, embed=embed)

        except Exception as e:
            import traceback; traceback.print_exc()
            await safe_send(ctx.channel, f"❌ Erreur dans !combat : `{e}`")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CombatCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
