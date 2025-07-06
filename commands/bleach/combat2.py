# ────────────────────────────────────────────────────────────────────────────────
# 📌 combat.py — Commande interactive !combat
# Objectif : Simule un combat entre 2 personnages de Bleach avec stats, énergie et effets.
# Catégorie : Bleach
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import random
import json
import os

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des personnages
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_personnages.json")

def load_personnages():
    """Charge les personnages depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🧰 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
def init_personnage(perso):
    """Initialise les stats d’un personnage pour le combat."""
    perso["energie"] = 100
    perso["vie"] = 100
    perso["status"] = None
    perso["status_duree"] = 0
    for atk in perso["attaques"]:
        atk["utilisé"] = False

def formater_etat(p):
    """Retourne l'état formaté d’un personnage pour l'affichage."""
    coeur = f"❤️ {max(p['vie'], 0)}"
    batterie = f"🔋 {p['energie']}"
    if p["status"] == "gel":
        statut = f"❄️ Gelé ({p['status_duree']} tour{'s' if p['status_duree'] > 1 else ''})"
    elif p["status"] == "confusion":
        statut = f"💫 Confus ({p['status_duree']} tours)"
    elif p["status"] == "poison":
        statut = f"☠️ Empoisonné ({p['status_duree']} tours)"
    else:
        statut = "❌"
    return f"{p['nom']} — {coeur} | {batterie} | {statut}"

def appliquer_effet(attaque, cible, log):
    """Applique les effets spéciaux de l'attaque à la cible."""
    effet = attaque["effet"].lower()
    if effet in ["gel", "paralysie"]:
        cible["status"] = "gel"
        cible["status_duree"] = 1
        log += f"❄️ {cible['nom']} est gelé !\n"
    elif effet in ["confusion", "illusion"]:
        cible["status"] = "confusion"
        cible["status_duree"] = 2
        log += f"💫 {cible['nom']} est confus 2 tours !\n"
    elif effet in ["poison", "corrosion"]:
        cible["status"] = "poison"
        cible["status_duree"] = 3
        log += f"☠️ {cible['nom']} est empoisonné !\n"
    return log

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Combat2Command(commands.Cog):
    """
    Commande !combat — Simule un combat entre 2 personnages de Bleach avec stats, énergie et effets.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="combat2",
        help="Simule un combat entre 2 personnages de Bleach.",
        description="Lance un combat automatisé sur 5 tours entre 2 personnages tirés au hasard."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def combat(self, ctx: commands.Context):
        """Commande principale simulant un combat."""
        try:
            personnages = load_personnages()

            if len(personnages) < 2:
                return await ctx.send("❌ Pas assez de personnages dans le fichier.")

            p1, p2 = random.sample(personnages, 2)
            for p in (p1, p2): init_personnage(p)

            # Détermine l'ordre des tours en fonction de la mobilité
            tour_order = sorted([p1, p2], key=lambda p: p["stats"]["mobilité"] + random.randint(0, 10), reverse=True)
            log = f"**{p1['nom']} contre {p2['nom']} !**\n\n"

            for tour in range(1, 6):
                log += f"**🌀 __Tour {tour}__ 🌀**\n{formater_etat(p1)}\n{formater_etat(p2)}\n\n"
                for attaquant in tour_order:
                    defenseur = p2 if attaquant == p1 else p1

                    # Si mort, passe le tour
                    if attaquant["vie"] <= 0 or defenseur["vie"] <= 0:
                        continue

                    # Gère les effets de statut
                    if attaquant["status"] == "gel":
                        log += f"❄️ **{attaquant['nom']}** est gelé et ne peut pas agir.\n\n"
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None
                        continue

                    if attaquant["status"] == "confusion" and random.random() < 0.4:
                        log += f"💫 **{attaquant['nom']}** est confus et se blesse (10 PV) !\n\n"
                        attaquant["vie"] -= 10
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None
                        continue

                    if attaquant["status"] == "poison":
                        log += f"☠️ **{attaquant['nom']}** perd 5 PV à cause du poison.\n"
                        attaquant["vie"] -= 5
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None

                    # Choix de l'attaque possible
                    possibles = [
                        a for a in attaquant["attaques"]
                        if a["cout"] <= attaquant["energie"] and (a["type"] != "ultime" or not a["utilisé"])
                    ]
                    if not possibles:
                        log += f"💤 **{attaquant['nom']}** est à court d'énergie.\n\n"
                        continue

                    attaque = random.choice(possibles)
                    if attaque["type"] == "ultime":
                        attaque["utilisé"] = True

                    # Esquive et contre-attaque
                    esquive_chance = min(defenseur["stats"]["mobilité"] / 40 + random.uniform(0, 0.2), 0.5)
                    tentative = random.random()
                    cout_esquive = 50 if attaque["type"] == "ultime" else 10

                    if tentative < esquive_chance and defenseur["energie"] >= cout_esquive:
                        defenseur["energie"] -= cout_esquive
                        log += f"💨 **{defenseur['nom']}** esquive **{attaque['nom']}** !\n"
                        if random.random() < 0.2:
                            contre = 10 + defenseur["stats"]["attaque"] // 2
                            attaquant["vie"] -= contre
                            log += f"🔁 Contre-attaque ! {attaquant['nom']} subit {contre} dégâts !\n"
                            if attaquant["vie"] <= 0:
                                log += f"\n🏆 **{defenseur['nom']} gagne par contre-attaque !**"
                                return await self.send_embed_log(ctx, log)
                        log += "\n"
                        continue

                    elif tentative < esquive_chance:
                        log += f"⚡ {defenseur['nom']} voulait esquiver mais manque d'énergie !\n"

                    # Calcul des dégâts
                    base = attaque["degats"]
                    bonus = (
                        attaquant["stats"]["attaque"] +
                        attaquant["stats"]["force"] -
                        defenseur["stats"]["défense"] +
                        attaquant["stats"]["pression"] // 5
                    )
                    total = base + max(0, bonus)

                    if random.random() < min(0.1 + attaquant["stats"]["force"] / 50, 0.4):
                        total = int(total * 1.5)
                        log += "💥 Coup critique ! "

                    defenseur["vie"] -= total
                    attaquant["energie"] -= attaque["cout"]

                    log += (
                        f"💥 **{attaquant['nom']}** utilise **{attaque['nom']}**\n"
                        f"➡️ {defenseur['nom']} perd {total} PV\n"
                    )

                    log = appliquer_effet(attaque, defenseur, log)

                    if defenseur["vie"] <= 0:
                        log += f"\n🏆 **{attaquant['nom']} remporte le combat par KO !**"
                        return await self.send_embed_log(ctx, log)

                    log += "\n"

            gagnant = p1 if p1["vie"] > p2["vie"] else p2
            log += f"🏁 Fin du combat, vainqueur : **{gagnant['nom']}** !"
            await self.send_embed_log(ctx, log)

        except Exception as e:
            print(f"[ERREUR !combat] {e}")
            await ctx.send("❌ Une erreur est survenue lors de la simulation du combat.")

    async def send_embed_log(self, ctx, log: str):
        """Envoie le log dans un embed, tronque si trop long."""
        MAX_EMBED_DESC = 6000
        if len(log) > MAX_EMBED_DESC:
            log = log[:MAX_EMBED_DESC - 50] + "\n...[log tronqué]..."

        embed = discord.Embed(
            title="🗡️ {nom1} vs {nom2}",
            description=log,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Combat2Command(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
