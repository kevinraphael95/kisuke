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
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CombatCommand(commands.Cog):
    """
    Commande !combat — Simule un combat entre 2 personnages de Bleach avec stats, énergie et effets.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="combat",
        help="Simule un combat entre 2 personnages de Bleach.",
        description="Lance un combat automatisé sur 5 tours entre 2 personnages tirés au hasard."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def combat(self, ctx: commands.Context):
        """Commande principale simulant un combat."""

        def format_etat_ligne(p: dict) -> str:
            coeur = f"❤️ {max(p['vie'], 0)}"
            batterie = f"🔋 {p['energie']}"
            if p["status"] == "gel":
                statut = f"❄️ Gelé ({p['status_duree']} tour{'s' if p['status_duree'] > 1 else ''})"
            elif p["status"] == "confusion":
                statut = f"💫 Confus ({p['status_duree']} tours)"
            elif p["status"] == "poison":
                statut = f"☠️ Empoisonné ({p['status_duree']} tours)"
            else:
                statut = "Aucun effet"
            return f"{p['nom']} — {coeur} | {batterie} | {statut}"

        try:
            personnages = load_personnages()

            if len(personnages) < 2:
                await ctx.send("❌ Pas assez de personnages dans le fichier.")
                return

            p1, p2 = random.sample(personnages, 2)
            for p in (p1, p2):
                p["energie"] = 100
                p["vie"] = 100
                p["status"] = None
                p["status_duree"] = 0
                for atk in p["attaques"]:
                    atk["utilisé"] = False

            p1_init = p1["stats"]["mobilité"] + random.randint(0, 10)
            p2_init = p2["stats"]["mobilité"] + random.randint(0, 10)
            tour_order = [p1, p2] if p1_init >= p2_init else [p2, p1]

            log = f"⚔️ **Combat entre {p1['nom']} et {p2['nom']} !**\n\n"

            for tour in range(1, 6):
                log += f"**🌀─────── Tour {tour} ───────🌀**\n"
                log += f"{format_etat_ligne(p1)}\n{format_etat_ligne(p2)}\n\n"

                for attaquant in tour_order:
                    defenseur = p1 if attaquant == p2 else p2

                    if attaquant["vie"] <= 0 or defenseur["vie"] <= 0:
                        continue

                    if attaquant["status"] == "gel":
                        log += f"❄️ **{attaquant['nom']}** est gelé et ne peut pas agir.\n\n"
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None
                        continue

                    if attaquant["status"] == "confusion":
                        if random.random() < 0.4:
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

                    esquive_chance = min(defenseur["stats"]["mobilité"] / 40 + random.uniform(0, 0.2), 0.5)
                    tentative_esquive = random.random()
                    cout_esquive = 50 if attaque["type"] == "ultime" else 10

                    if tentative_esquive < esquive_chance:
                        if defenseur["energie"] >= cout_esquive:
                            defenseur["energie"] -= cout_esquive
                            log += f"💨 **{defenseur['nom']}** esquive **{attaque['nom']}** !\n"
                            if random.random() < 0.2:
                                contre = 10 + defenseur["stats"]["attaque"] // 2
                                attaquant["vie"] -= contre
                                log += f"🔁 Contre-attaque ! {attaquant['nom']} subit {contre} dégâts !\n"
                                if attaquant["vie"] <= 0:
                                    log += f"\n🏆 **{defenseur['nom']} gagne par contre-attaque !**"
                                    await self.send_embed_log(ctx, log)
                                    return
                            log += "\n"
                            continue
                        else:
                            log += f"⚡ {defenseur['nom']} voulait esquiver mais manque d'énergie !\n"

                    base = attaque["degats"]
                    bonus = (
                        attaquant["stats"]["attaque"]
                        + attaquant["stats"]["force"]
                        - defenseur["stats"]["défense"]
                        + attaquant["stats"]["pression"] // 5
                    )
                    total = base + max(0, bonus)

                    if random.random() < min(0.1 + attaquant["stats"]["force"] / 50, 0.4):
                        total = int(total * 1.5)
                        log += "💥 Coup critique !"


                    if "bouclier" in defenseur and defenseur["bouclier"]:
                        total = total // 2
                        log += "🛡️ Bouclier actif : dégâts réduits de moitié !\n"
                        defenseur["bouclier"] = False  # effet consommé

                    defenseur["vie"] -= total
                    attaquant["energie"] -= attaque["cout"]

                    log += (
                        f"💥 **{attaquant['nom']}** utilise **{attaque['nom']}**\n"
                        f"➡️ {defenseur['nom']} perd {total} PV\n"
                    )

                    effet = attaque["effet"].lower()
                    if effet in ["gel", "paralysie"]:
                        defenseur["status"] = "gel"
                        defenseur["status_duree"] = 1
                        log += f"❄️ {defenseur['nom']} est gelé !\n"
                    elif effet in ["confusion", "illusion"]:
                        defenseur["status"] = "confusion"
                        defenseur["status_duree"] = 2
                        log += f"💫 {defenseur['nom']} est confus 2 tours !\n"
                    elif effet in ["poison", "corrosion"]:
                        defenseur["status"] = "poison"
                        defenseur["status_duree"] = 3
                        log += f"☠️ {defenseur['nom']} est empoisonné !\n"

                    elif effet == "soin":
                        soin = min(30 + attaquant["stats"]["reiatsu"] // 2, 50)
                        attaquant["vie"] = min(attaquant["vie"] + soin, 100)
                        log += f"💖 {attaquant['nom']} se soigne de {soin} PV !\n"
                    elif effet == "bouclier":
                        attaquant["bouclier"] = True
                        log += f"🛡️ {attaquant['nom']} est protégé ! (Demi-dégâts ce tour)\n"


                    if defenseur["vie"] <= 0:
                        log += f"\n🏆 **{attaquant['nom']} remporte le combat par KO !**"
                        await self.send_embed_log(ctx, log)
                        return

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
            title="🗡️ Résultat du combat",
            description=log,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CombatCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
