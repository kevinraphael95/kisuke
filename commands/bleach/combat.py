# ────────────────────────────────────────────────────────────────────────────────
# 📌 combat.py — Commande interactive !combat
# Objectif : Simule un combat immersif entre 2 personnages de Bleach façon Pokémon
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
# 🔧 Types et efficacité
# ────────────────────────────────────────────────────────────────────────────────
# Multiplicateurs de type (attaque vs cible)
TYPE_EFFICACITE = {
    # Normal
    ("Normal", "Roche"): 0.5, ("Normal", "Spectre"): 0,
    # Feu
    ("Feu", "Feu"): 0.5, ("Feu", "Eau"): 0.5, ("Feu", "Plante"): 2, ("Feu", "Glace"): 2, ("Feu", "Insecte"): 2, ("Feu", "Roche"): 0.5, ("Feu", "Acier"): 2,
    # Eau
    ("Eau", "Feu"): 2, ("Eau", "Eau"): 0.5, ("Eau", "Plante"): 0.5, ("Eau", "Sol"): 2, ("Eau", "Roche"): 2, ("Eau", "Dragon"): 0.5,
    # Plante
    ("Plante", "Eau"): 2, ("Plante", "Feu"): 0.5, ("Plante", "Plante"): 0.5, ("Plante", "Poison"): 0.5, ("Plante", "Vol"): 0.5, ("Plante", "Sol"): 2, ("Plante", "Roche"): 2, ("Plante", "Insecte"): 0.5, ("Plante", "Dragon"): 0.5, ("Plante", "Acier"): 0.5,
    # Électrik
    ("Électrik", "Eau"): 2, ("Électrik", "Électrik"): 0.5, ("Électrik", "Plante"): 0.5, ("Électrik", "Sol"): 0, ("Électrik", "Vol"): 2, ("Électrik", "Dragon"): 0.5,
    # Glace
    ("Glace", "Plante"): 2, ("Glace", "Feu"): 0.5, ("Glace", "Eau"): 0.5, ("Glace", "Glace"): 0.5, ("Glace", "Sol"): 2, ("Glace", "Vol"): 2, ("Glace", "Dragon"): 2, ("Glace", "Acier"): 0.5,
    # Combat
    ("Combat", "Normal"): 2, ("Combat", "Glace"): 2, ("Combat", "Roche"): 2, ("Combat", "Ténèbres"): 2, ("Combat", "Acier"): 2, ("Combat", "Poison"): 0.5, ("Combat", "Vol"): 0.5, ("Combat", "Psy"): 0.5, ("Combat", "Fée"): 0.5,
    # Poison
    ("Poison", "Plante"): 2, ("Poison", "Poison"): 0.5, ("Poison", "Sol"): 0.5, ("Poison", "Roche"): 0.5, ("Poison", "Spectre"): 0.5, ("Poison", "Acier"): 0,
    # Sol
    ("Sol", "Feu"): 2, ("Sol", "Électrik"): 2, ("Sol", "Plante"): 0.5, ("Sol", "Poison"): 2, ("Sol", "Vol"): 0, ("Sol", "Roche"): 2, ("Sol", "Acier"): 2,
    # Vol
    ("Vol", "Plante"): 2, ("Vol", "Électrik"): 0.5, ("Vol", "Combat"): 2, ("Vol", "Roche"): 0.5, ("Vol", "Insecte"): 2,
    # Psy
    ("Psy", "Combat"): 2, ("Psy", "Poison"): 2, ("Psy", "Psy"): 0.5, ("Psy", "Ténèbres"): 0, ("Psy", "Acier"): 0.5,
    # Insecte
    ("Insecte", "Plante"): 2, ("Insecte", "Feu"): 0.5, ("Insecte", "Combat"): 0.5, ("Insecte", "Poison"): 0.5, ("Insecte", "Vol"): 0.5, ("Insecte", "Spectre"): 0.5, ("Insecte", "Ténèbres"): 2, ("Insecte", "Acier"): 0.5, ("Insecte", "Fée"): 0.5,
    # Roche
    ("Roche", "Feu"): 2, ("Roche", "Glace"): 2, ("Roche", "Combat"): 0.5, ("Roche", "Sol"): 0.5, ("Roche", "Vol"): 2, ("Roche", "Acier"): 0.5,
    # Fantôme
    ("Spectre", "Normal"): 0, ("Spectre", "Psy"): 2, ("Spectre", "Spectre"): 2, ("Spectre", "Ténèbres"): 0.5,
    # Dragon
    ("Dragon", "Dragon"): 2, ("Dragon", "Acier"): 0.5, ("Dragon", "Fée"): 0,
    # Ténèbres
    ("Ténèbres", "Psy"): 2, ("Ténèbres", "Spectre"): 2, ("Ténèbres", "Combat"): 0.5, ("Ténèbres", "Fée"): 0.5,
    # Acier
    ("Acier", "Glace"): 2, ("Acier", "Roche"): 2, ("Acier", "Fée"): 2, ("Acier", "Feu"): 0.5, ("Acier", "Eau"): 0.5, ("Acier", "Électrik"): 0.5, ("Acier", "Acier"): 0.5,
    # Fée
    ("Fée", "Combat"): 2, ("Fée", "Dragon"): 2, ("Fée", "Ténèbres"): 2, ("Fée", "Feu"): 0.5, ("Fée", "Poison"): 0.5, ("Fée", "Acier"): 0.5
}

def multiplier_type(attaque_type, cible_type):
    return TYPE_EFFICACITE.get((attaque_type, cible_type), 1)


# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Fonctions utilitaires du combat
# ────────────────────────────────────────────────────────────────────────────────
def init_combat(p: dict):
    """Initialise un personnage pour le combat."""
    p = p.copy()
    p["pv"] = 100
    p["endurance"] = 100
    p["forme_actuelle"] = "Normal"
    p["bonus_defense"] = 0  # pour les attaques défensives temporaires
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
    return {"nom": "Attaque faible", "type": "Normal", "categorie": "Offensive", "puissance": 10, "cout_endurance": 0}

def appliquer_degats(cible: dict, degats: int, narratif: list, attaquant: dict, attaque: dict):
    """Applique les dégâts selon la catégorie et le type."""
    if attaque["categorie"] == "Soin":
        cible["pv"] += attaque["puissance"]
        narratif.append(f"💖 **{attaquant['nom']}** utilise *{attaque['nom']}* et soigne **{attaque['puissance']} PV** ! "
                        f"(PV : {cible['pv']})")
        return narratif

    if attaque["categorie"] == "Défensive":
        attaquant["bonus_defense"] += attaque["puissance"] // 2
        narratif.append(f"🛡️ **{attaquant['nom']}** utilise *{attaque['nom']}* et augmente sa défense temporairement !")
        return narratif

    # Offensive ou Contrôle
    mult = multiplier_type(attaque["type"], cible["type"])
    degats_reels = max(5, int((degats - cible.get("bonus_defense", 0)) * mult))
    cible["pv"] -= degats_reels
    narratif.append(f"💥 **{attaquant['nom']}** utilise *{attaque['nom']}* "
                    f"(Type {attaque['type']}, Catégorie {attaque['categorie']}) "
                    f"et inflige **{degats_reels} PV** à **{cible['nom']}** ! "
                    f"(PV restants : {cible['pv']})")
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
    """Commande !combat — Combat immersif entre 2 personnages de Bleach façon Pokémon."""

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

            narratif = [f"⚔️ **Combat : {p1['nom']} (Type {p1['type']}) vs {p2['nom']} (Type {p2['type']})** ⚔️\n"]

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
                    degats = attaque["puissance"] + attaquant["stats_base"]["attaque"] - defenseur["stats_base"]["defense"]

                    narratif = appliquer_degats(defenseur, degats, narratif, attaquant, attaque)
                    attaquant["endurance"] -= attaque.get("cout_endurance", 0)

                    # Vérification forme suivante
                    fs = forme_suivante(attaquant)
                    if fs:
                        narratif.append(fs)

                    # Reset bonus_defense après utilisation
                    if attaque["categorie"] != "Défensive":
                        defenseur["bonus_defense"] = 0

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
