# ────────────────────────────────────────────────────────────────────────────────
# 📌 versus.py — Combat interactif contre le bot
# Objectif : Combat style Pokémon entre joueur et bot (avec attaques choisies)
# Catégorie : Bleach
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
import random, os, json
from utils.discord_utils import safe_send

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Données du jeu
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
    p["pv"] = p["stats_base"]["total_stats"] // 3
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
        narratif.append(f"{CATEGORIE_EMOJI['Soin']} **{a['nom']}** se soigne de {soin} PV !")
        return
    degats, mult, crit = calcul_degats(a, d, atk)
    d["pv"] -= degats
    txt = f"{CATEGORIE_EMOJI['Offensive']} **{a['nom']}** utilise *{atk['nom']}* et inflige {degats} PV à **{d['nom']}** !"
    if crit: txt += " ⚡ Coup critique !"
    if mult > 1: txt += " 💥 Super efficace !"
    elif mult < 1: txt += " ⚠️ Pas très efficace..."
    narratif.append(txt)
    if "statut" in atk:
        d["statut"] = atk["statut"]

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal — /versus
# ────────────────────────────────────────────────────────────────────────────────
class VersusCommand(commands.Cog):
    """Combat interactif contre le bot"""
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="versus", description="Affronte le bot dans un combat Pokémon-style !")
    async def slash_versus(self, interaction: discord.Interaction):
        await self.start_versus(interaction)

    @commands.command(name="versus")
    async def prefix_versus(self, ctx: commands.Context):
        await self.start_versus(ctx)

    async def start_versus(self, source):
        channel = source.channel if isinstance(source, commands.Context) else source.channel
        user = source.author if isinstance(source, commands.Context) else source.user

        persos = [load_character(n) for n in list_characters()]
        persos = [p for p in persos if p]
        if not persos:
            return await safe_send(channel, "❌ Aucun personnage disponible.")

        # Étape 1 — Choix du perso par le joueur
        options = [discord.SelectOption(label=p["nom"], description=p["description"][:80]) for p in persos]

        select = discord.ui.Select(placeholder="Choisis ton personnage...", options=options[:25])

        view = discord.ui.View()
        view.add_item(select)

        msg = await safe_send(channel, f"{user.mention}, choisis ton personnage :", view=view)

        async def select_callback(interaction):
            if interaction.user.id != user.id:
                return await interaction.response.send_message("Ce n’est pas ton combat !", ephemeral=True)
            nom = select.values[0]
            joueur = init_combat(load_character(nom))
            bot_perso = init_combat(random.choice(persos))
            await self.run_versus(channel, user, joueur, bot_perso)
            view.stop()

        select.callback = select_callback

    async def run_versus(self, channel, user, p1, p2):
        narratif = [f"⚔️ **{p1['nom']} (toi)** vs **{p2['nom']} (bot)** ⚔️\n"]

        while p1["pv"] > 0 and p2["pv"] > 0:
            # Embed état
            embed = discord.Embed(
                title=f"🗡️ {p1['nom']} vs {p2['nom']}",
                description=f"❤️ {p1['nom']} : {p1['pv']} PV\n💀 {p2['nom']} : {p2['pv']} PV\n\nChoisis ton attaque :",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=p1["image"])
            embed.set_image(url=p2["image"])

            # Boutons d’attaque
            view = discord.ui.View(timeout=60)
            attaques = attaque_disponible(p1)[:4]

            for atk in attaques:
                async def callback(interaction, atk=atk):
                    if interaction.user.id != user.id:
                        return await interaction.response.send_message("Ce n’est pas ton combat !", ephemeral=True)
                    atk["PP"] -= 1
                    appliquer_attaque(p1, p2, atk, narratif)
                    if p2["pv"] <= 0:
                        await interaction.response.edit_message(content=f"🏆 **{p1['nom']}** remporte le combat !", view=None)
                        return
                    # Tour du bot
                    bot_atk = random.choice(attaque_disponible(p2))
                    appliquer_attaque(p2, p1, bot_atk, narratif)
                    if p1["pv"] <= 0:
                        await interaction.response.edit_message(content=f"💀 **{p2['nom']}** (bot) gagne !", view=None)
                        return
                    await self.run_versus(channel, user, p1, p2)
                    view.stop()

                view.add_item(discord.ui.Button(label=atk["nom"], style=discord.ButtonStyle.primary, custom_id=atk["nom"]))
                view.children[-1].callback = callback

            await safe_send(channel, embed=embed, view=view)
            break

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = VersusCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun&Random"
    await bot.add_cog(cog)


