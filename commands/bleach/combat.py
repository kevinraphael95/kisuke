# ────────────────────────────────────────────────────────────────────────────────
# 📌 combat.py — Commande interactive !combat
# Objectif : Simule un combat entre 2 personnages de Bleach avec stats, énergie et effets
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
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_personnages.json")

def load_personnages():
    """Charge les personnages depuis le fichier JSON."""
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonction utilitaire — Format de l’état du personnage
# ────────────────────────────────────────────────────────────────────────────────
def format_etat_ligne(p: dict) -> str:
    """Formate une ligne d'état du personnage."""
    coeur = f"❤️ {max(p['vie'], 0)} PV"
    batterie = f"🔋 {p['energie']} énergie"
    if p["status"] == "gel":
        statut = f"❄️ Gelé ({p['status_duree']} tour{'s' if p['status_duree'] > 1 else ''})"
    elif p["status"] == "confusion":
        statut = f"💫 Confus ({p['status_duree']} tours)"
    elif p["status"] == "poison":
        statut = f"☠️ Empoisonné ({p['status_duree']} tours)"
    else:
        statut = "✅ Aucun effet"
    return f"{p['nom']} — {coeur} | {batterie} | {statut}"

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Cog principal — CombatCommand
# ────────────────────────────────────────────────────────────────────────────────
class CombatCommand(commands.Cog):
    """
    Commande !combat — Simule un combat entre 2 personnages de Bleach avec stats, énergie et effets.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="combat",
        help="Simule un combat entre 2 personnages de Bleach avec stats, énergie et effets.",
        description="Lance un combat automatisé sur 5 tours entre 2 personnages tirés au hasard."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def combat(self, ctx: commands.Context):
        try:
            personnages = load_personnages()
            if len(personnages) < 2:
                await ctx.send("❌ Pas assez de personnages dans le fichier.")
                return

            p1, p2 = random.sample(personnages, 2)
            for p in (p1, p2):
                p.update({"energie": 100, "vie": 100, "status": None, "status_duree": 0})
                for atk in p["attaques"]:
                    atk["utilisé"] = False

            p1_init = p1["stats"]["mobilité"] + random.randint(0, 10)
            p2_init = p2["stats"]["mobilité"] + random.randint(0, 10)
            tour_order = [p1, p2] if p1_init >= p2_init else [p2, p1]

            embed = discord.Embed(
                title=f"⚔️ Combat : {p1['nom']} VS {p2['nom']}",
                color=discord.Color.purple()
            )

            logs_par_tour = []

            for tour in range(1, 6):
                texte_tour = f"{format_etat_ligne(p1)}\n{format_etat_ligne(p2)}\n\n"
                
                for attaquant in tour_order:
                    defenseur = p1 if attaquant == p2 else p2
                    if attaquant["vie"] <= 0 or defenseur["vie"] <= 0:
                        continue

                    if attaquant["status"] == "gel":
                        texte_tour += f"❄️ **{attaquant['nom']}** est gelé et ne peut pas agir.\n\n"
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None
                        continue

                    if attaquant["status"] == "confusion":
                        if random.random() < 0.4:
                            texte_tour += f"💫 **{attaquant['nom']}** est confus et se blesse (10 PV) !\n\n"
                            attaquant["vie"] -= 10
                            attaquant["status_duree"] -= 1
                            if attaquant["status_duree"] <= 0:
                                attaquant["status"] = None
                            continue

                    if attaquant["status"] == "poison":
                        texte_tour += f"☠️ **{attaquant['nom']}** perd 5 PV à cause du poison.\n"
                        attaquant["vie"] -= 5
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None

                    possibles = [
                        a for a in attaquant["attaques"]
                        if a["cout"] <= attaquant["energie"] and (a["type"] != "ultime" or not a["utilisé"])
                    ]
                    if not possibles:
                        texte_tour += f"💤 **{attaquant['nom']}** est à court d'énergie.\n\n"
                        continue

                    attaque = random.choice(possibles)
                    if attaque["type"] == "ultime":
                        attaque["utilisé"] = True

                    esquive_chance = min(defenseur["stats"]["mobilité"] / 40 + random.uniform(0, 0.2), 0.5)
                    tentative_esquive = random.random()
                    cout_esquive = 50 if attaque["type"] == "ultime" else 10

                    if tentative_esquive < esquive_chance and defenseur["energie"] >= cout_esquive:
                        defenseur["energie"] -= cout_esquive
                        texte_tour += f"💨 **{defenseur['nom']}** esquive **{attaque['nom']}** ! (-{cout_esquive} énergie)\n"
                        if random.random() < 0.2:
                            contre = 10 + defenseur["stats"]["attaque"] // 2
                            attaquant["vie"] -= contre
                            texte_tour += f"🔁 Contre-attaque ! **{attaquant['nom']}** subit {contre} dégâts !\n"
                            if attaquant["vie"] <= 0:
                                texte_tour += f"\n🏆 **{defenseur['nom']} gagne par contre-attaque !**"
                                embed.add_field(name=f"Fin du combat (tour {tour})", value=texte_tour, inline=False)
                                await ctx.send(embed=embed)
                                return
                        texte_tour += "\n"
                        continue

                    base = attaque["degats"]
                    bonus = (
                        attaquant["stats"]["attaque"] + attaquant["stats"]["force"]
                        - defenseur["stats"]["défense"] + attaquant["stats"]["pression"] // 5
                    )
                    total = base + max(0, bonus)

                    if random.random() < min(0.1 + attaquant["stats"]["force"] / 50, 0.4):
                        total = int(total * 1.5)
                        texte_tour += "💥 Coup critique !\n"

                    defenseur["vie"] -= total
                    attaquant["energie"] -= attaque["cout"]

                    texte_tour += (
                        f"💥 **{attaquant['nom']}** utilise **{attaque['nom']}** "
                        f"(coût : {attaque['cout']}, dégâts : {base}+bonus)\n"
                        f"➡️ {defenseur['nom']} perd {total} PV\n"
                    )

                    effet = attaque["effet"].lower()
                    if effet in ["gel", "paralysie"]:
                        defenseur["status"] = "gel"
                        defenseur["status_duree"] = 1
                        texte_tour += f"❄️ **{defenseur['nom']}** est gelé !\n"
                    elif effet in ["confusion", "illusion"]:
                        defenseur["status"] = "confusion"
                        defenseur["status_duree"] = 2
                        texte_tour += f"💫 **{defenseur['nom']}** est confus 2 tours !\n"
                    elif effet in ["poison", "corrosion"]:
                        defenseur["status"] = "poison"
                        defenseur["status_duree"] = 3
                        texte_tour += f"☠️ **{defenseur['nom']}** est empoisonné !\n"

                    if defenseur["vie"] <= 0:
                        texte_tour += f"\n🏆 **{attaquant['nom']} remporte le combat !**"
                        logs_par_tour.append(texte_tour)

                        for i, log_tour in enumerate(logs_par_tour, 1):
                            embed.add_field(name=f"Tour {i}", value=log_tour, inline=False)

                        embed.set_footer(text=f"🏁 Combat terminé au tour {tour}")
                        await ctx.send(embed=embed)
                        return

                logs_par_tour.append(texte_tour + "\n") 

            for i, log_tour in enumerate(logs_par_tour, 1):
                embed.add_field(name=f"Tour {i}", value=log_tour, inline=False)

            # 🔚 Résultat final du combat
            if p1["vie"] > p2["vie"]:
                resultat = f"🏁 **Victoire aux points de {p1['nom']} !** ({p1['vie']} PV restants contre {p2['vie']} PV)"
            elif p2["vie"] > p1["vie"]:
                resultat = f"🏁 **Victoire aux points de {p2['nom']} !** ({p2['vie']} PV restants contre {p1['vie']} PV)"
            else:
                resultat = "🤝 **Égalité parfaite après 5 tours !**"

            embed.add_field(name="🎯 Résultat final", value=resultat, inline=False)
            embed.set_footer(text="⚔️ Combat terminé après 5 tours")


            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : `{e}`")

# ────────────────────────────────────────────────────────────────────────────────
# 🚀 Setup de la commande
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CombatCommand(bot)
    for command in cog.get_commands():
        command.category = "Bleach"
    await bot.add_cog(cog)
    print("✅ Cog chargé : CombatCommand (catégorie = Bleach)")
