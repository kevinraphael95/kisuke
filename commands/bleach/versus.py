# ────────────────────────────────────────────────────────────────────────────────
# 📌 versus_bot.py — Combat interactif contre le bot
# Objectif : Combat style Pokémon complet avec statuts et formes évolutives
# Catégorie : Bleach
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
class VersusBotCommand(commands.Cog):
    """Combat interactif contre le bot avec boutons"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="versus", description="⚔️ Combat interactif contre le bot.")
    async def slash_versus(self, interaction: discord.Interaction):
        await self.start_versus(interaction)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="versus")
    async def prefix_versus(self, ctx: commands.Context):
        await self.start_versus(ctx)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔧 Lancement du choix de personnage
    # ────────────────────────────────────────────────────────────────────────────
    async def start_versus(self, source):
        channel = source.channel if isinstance(source, commands.Context) else source.channel
        user = source.author if isinstance(source, commands.Context) else source.user

        persos = [load_character(n) for n in list_characters()]
        persos = [p for p in persos if p]
        if not persos:
            return await safe_send(channel, "❌ Aucun personnage disponible.")

        options = [discord.SelectOption(label=p["nom"], description=p.get("description","")[:80]) for p in persos]
        select = discord.ui.Select(placeholder="Choisis ton personnage...", options=options[:25])
        view = discord.ui.View()
        view.add_item(select)

        async def select_callback(interaction: discord.Interaction):
            if interaction.user.id != user.id:
                return await interaction.response.send_message("Ce n’est pas ton combat !", ephemeral=True)

            nom = select.values[0]
            joueur = init_combat(load_character(nom))
            bot_perso = init_combat(random.choice(persos))

            # Embed du premier tour
            embed = discord.Embed(
                title=f"🗡️ {joueur['nom']} vs {bot_perso['nom']}",
                description=f"❤️ {joueur['nom']} : {joueur['pv']} PV\n💀 {bot_perso['nom']} : {bot_perso['pv']} PV\n\nChoisis ton attaque :",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=joueur["image"])
            embed.set_image(url=bot_perso["image"])

            # Crée la view avec boutons
            view_attack = self.create_attack_buttons(joueur, bot_perso, interaction)

            await interaction.response.send_message(content=f"⚔️ **Combat commencé !**", embed=embed, view=view_attack)
            view.stop()

        select.callback = select_callback

        if isinstance(source, discord.Interaction):
            await source.response.send_message(f"{user.mention}, choisis ton personnage :", view=view)
        else:
            await safe_send(channel, f"{user.mention}, choisis ton personnage :", view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔧 Création de boutons pour les attaques
    # ────────────────────────────────────────────────────────────────────────────
    def create_attack_buttons(self, p1, p2, interaction):
        view = discord.ui.View(timeout=None)
        narratif = []

        for atk in attaque_disponible(p1)[:4]:
            button = discord.ui.Button(label=atk["nom"], style=discord.ButtonStyle.primary)
            async def callback(i: discord.Interaction, atk=atk):
                if i.user.id != interaction.user.id:
                    return await i.response.send_message("Ce n’est pas ton combat !", ephemeral=True)

                atk["PP"] -= 1
                appliquer_attaque(p1, p2, atk, narratif)
                fs = forme_suivante(p1)
                if fs: narratif.append(fs)

                # Vérification victoire joueur
                if p2["pv"] <= 0:
                    await i.response.edit_message(content=f"🏆 **{p1['nom']}** remporte le combat !", embed=None, view=None)
                    return

                # Tour bot
                bot_atk = random.choice(attaque_disponible(p2))
                appliquer_attaque(p2, p1, bot_atk, narratif)
                fs = forme_suivante(p2)
                if fs: narratif.append(fs)

                # Vérification victoire bot
                if p1["pv"] <= 0:
                    await i.response.edit_message(content=f"💀 **{p2['nom']}** (bot) gagne !", embed=None, view=None)
                    return

                # Mise à jour embed
                embed = discord.Embed(
                    title=f"🗡️ {p1['nom']} vs {p2['nom']}",
                    description=f"❤️ {p1['nom']} : {p1['pv']} PV\n💀 {p2['nom']} : {p2['pv']} PV\n\nChoisis ton attaque :",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=p1["image"])
                embed.set_image(url=p2["image"])

                await i.response.edit_message(embed=embed, view=view)

            button.callback = callback
            view.add_item(button)

        return view

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = VersusBotCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
