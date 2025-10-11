# ────────────────────────────────────────────────────────────────────────────────
# 📌 combat.py — Commande interactive !combat
# Objectif : Simule un combat entre 2 personnages de Bleach avec stats, endurance et effets.
# Catégorie : Bleach
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, button
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
    p["status"] = None
    return p

def formater_etat(p: dict) -> str:
    return f"**{p['nom']} ({p['forme_actuelle']})** — ❤️ {p['pv']} PV | 🔋 {p['endurance']} Endurance"

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

def appliquer_degats(cible: dict, degats: int, log: str) -> str:
    cible["pv"] -= degats
    log += f"💥 {cible['nom']} subit {degats} dégâts (PV restants: {cible['pv']})\n"
    return log

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue interactive : Bouton Nouveau Combat
# ────────────────────────────────────────────────────────────────────────────────
class CombatView(View):
    def __init__(self, persos, message):
        super().__init__(timeout=60)
        self.persos = persos
        self.message = message

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass

    @button(label="⚔️ Nouveau combat", style=discord.ButtonStyle.red)
    async def nouveau_combat(self, interaction: discord.Interaction, button: discord.ui.Button):
        p1, p2 = random.sample(self.persos, 2)
        await self._combat(p1, p2)
        await interaction.response.defer()

    async def _combat(self, p1_data, p2_data):
        p1, p2 = init_combat(p1_data), init_combat(p2_data)
        log = f"⚔️ **Combat : {p1['nom']} vs {p2['nom']}** ⚔️\n\n"
        tour = 1
        tour_order = sorted([p1, p2], key=lambda x: x["stats_base"]["rapidite"] + random.randint(0, 10), reverse=True)

        while p1["pv"] > 0 and p2["pv"] > 0:
            log += f"🌀 __Tour {tour}__ 🌀\n"
            log += f"{formater_etat(p1)}\n{formater_etat(p2)}\n\n"
            for attaquant in tour_order:
                defenseur = p2 if attaquant == p1 else p1
                if attaquant["pv"] <= 0 or defenseur["pv"] <= 0:
                    continue

                dispo = attaque_disponible(attaquant)
                if dispo:
                    attaque = random.choice(dispo)
                else:
                    attaque = attaque_faible(attaquant)

                degats = attaque["puissance"] + attaquant["stats_base"]["attaque"] - defenseur["stats_base"]["defense"]
                degats = max(5, degats)
                log = appliquer_degats(defenseur, degats, log)
                attaquant["endurance"] -= attaque.get("cout_endurance", 0)

                # Chance de passer à la forme suivante
                formes = list(attaquant["formes"].keys())
                idx = formes.index(attaquant["forme_actuelle"])
                if idx < len(formes)-1 and random.random() < 0.15:
                    attaquant["forme_actuelle"] = formes[idx+1]
                    log += f"✨ {attaquant['nom']} passe en **{attaquant['forme_actuelle']}** !\n"

                if defenseur["pv"] <= 0:
                    log += f"\n🏆 {attaquant['nom']} remporte le combat !"
                    break
            break  # Stop après un tour complet
        if p1["pv"] > 0 and p2["pv"] > 0:
            gagnant = p1 if p1["pv"] > p2["pv"] else p2
            log += f"\n🏁 Fin du combat, vainqueur : **{gagnant['nom']}**"

        embed = discord.Embed(title=f"🗡️ {p1['nom']} vs {p2['nom']}", description=log, color=discord.Color.red())
        await self.message.edit(embed=embed, view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CombatCommand(commands.Cog):
    """Commande !combat — Simule un combat entre 2 personnages de Bleach avec stats et endurance."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="combat",
        help="⚔️ Simule un combat entre 2 personnages de Bleach."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def combat(self, ctx: commands.Context):
        persos = [load_character(n) for n in list_characters()]
        persos = [p for p in persos if p is not None]

        if len(persos) < 2:
            return await safe_send(ctx.channel, "❌ Pas assez de personnages pour le combat.")

        p1, p2 = random.sample(persos, 2)
        embed = discord.Embed(title="⚔️ Combat en cours...", description="Préparation du combat...", color=discord.Color.red())
        message = await safe_send(ctx.channel, embed=embed)
        view = CombatView(persos, message)
        await view._combat(p1, p2)
        await message.edit(view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CombatCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
