# ────────────────────────────────────────────────────────────────────────────────
# 📌 combat.py — Commande interactive !combat
# Objectif : Simule un combat entre 2 personnages de Bleach avec stats, énergie et effets.
# Catégorie : Fun
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
        help="Simule un combat entre 2 personnages de Bleach avec stats, énergie et effets.",
        description="Lance un combat automatisé sur 5 tours entre 2 personnages tirés au hasard."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def combat(self, ctx: commands.Context):
        """Commande principale simulant un combat."""

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

        try:
            # Chargement des personnages
            data_path = os.path.join("data", "bleach_personnages.json")
            with open(data_path, "r", encoding="utf-8") as f:
                personnages = json.load(f)

            if len(personnages) < 2:
                await ctx.send("❌ Pas assez de personnages dans le fichier.")
                return

            # Sélection de 2 personnages aléatoires
            p1, p2 = random.sample(personnages, 2)
            for p in (p1, p2):
                p["energie"] = 100
                p["vie"] = 100
                p["status"] = None
                p["status_duree"] = 0
                for atk in p["attaques"]:
                    atk["utilisé"] = False  # Empêche utilisation multiple d'ulti

            # Initiative selon mobilité + hasard
            p1_init = p1["stats"]["mobilité"] + random.randint(0, 10)
            p2_init = p2["stats"]["mobilité"] + random.randint(0, 10)
            tour_order = [p1, p2] if p1_init >= p2_init else [p2, p1]

            log = f"⚔️ **Combat entre {p1['nom']} et {p2['nom']} !**\n\n"

            # 5 tours maximum
            for tour in range(1, 6):
                log += f"🌀─────── Tour {tour} ───────🌀\n\n"
                log += f"{format_etat_ligne(p1)}\n{format_etat_ligne(p2)}\n\n"

                for attaquant in tour_order:
                    defenseur = p1 if attaquant == p2 else p2

                    if attaquant["vie"] <= 0 or defenseur["vie"] <= 0:
                        continue

                    # Gestion des statuts
                    if attaquant["status"] == "gel":
                        log += f"❄️ {attaquant['nom']} est gelé et ne peut pas agir.\n\n"
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None
                        continue

                    if attaquant["status"] == "confusion":
                        if random.random() < 0.4:
                            log += f"💫 {attaquant['nom']} est confus et se blesse (10 PV) !\n\n"
                            attaquant["vie"] -= 10
                            attaquant["status_duree"] -= 1
                            if attaquant["status_duree"] <= 0:
                                attaquant["status"] = None
                            continue

                    if attaquant["status"] == "poison":
                        log += f"☠️ {attaquant['nom']} perd 5 PV à cause du poison.\n"
                        attaquant["vie"] -= 5
                        attaquant["status_duree"] -= 1
                        if attaquant["status_duree"] <= 0:
                            attaquant["status"] = None

                    # Choix d'une attaque possible
                    possibles = [
                        a for a in attaquant["attaques"]
                        if a["cout"] <= attaquant["energie"] and (a["type"] != "ultime" or not a["utilisé"])
                    ]
                    if not possibles:
                        log += f"💤 {attaquant['nom']} est à court d'énergie.\n\n"
                        continue

                    attaque = random.choice(possibles)
                    if attaque["type"] == "ultime":
                        attaque["utilisé"] = True

                    # Tentative d'esquive
                    esquive_chance = min(defenseur["stats"]["mobilité"] / 40 + random.uniform(0, 0.2), 0.5)
                    tentative_esquive = random.random()
                    cout_esquive = 50 if attaque["type"] == "ultime" else 10

                    if tentative_esquive < esquive_chance:
                        if defenseur["energie"] >= cout_esquive:
                            defenseur["energie"] -= cout_esquive
                            log += f"💨 {defenseur['nom']} esquive **{attaque['nom']}** ! (-{cout_esquive} énergie)\n"
                            if random.random() < 0.2:
                                contre = 10 + defenseur["stats"]["attaque"] // 2
                                attaquant["vie"] -= contre
                                log += f"🔁 Contre-attaque ! {attaquant['nom']} subit {contre} dégâts !\n"
                                if attaquant["vie"] <= 0:
                                    log += f"\n🏆 **{defenseur['nom']} gagne par contre-attaque !**"
                                    await ctx.send(log)
                                    return
                            log += "\n"
                            continue
                        else:
                            log += f"⚡ {defenseur['nom']} voulait esquiver mais manque d'énergie !\n"

                    # Calcul des dégâts
                    base = attaque["degats"]
                    bonus = (
                        attaquant["stats"]["attaque"]
                        + attaquant["stats"]["force"]
                        - defenseur["stats"]["défense"]
                        + attaquant["stats"]["pression"] // 5
                    )
                    total = base + max(0, bonus)

                    # Critique
                    if random.random() < min(0.1 + attaquant["stats"]["force"] / 50, 0.4):
                        total = int(total * 1.5)
                        log += "💥 Coup critique !\n"

                    defenseur["vie"] -= total
                    attaquant["energie"] -= attaque["cout"]

                    log += (
                        f"💥 {attaquant['nom']} utilise **{attaque['nom']}** "
                        f"(coût : {attaque['cout']}, dégâts : {base}+bonus)\n"
                        f"➡️ {defenseur['nom']} perd {total} PV\n"
                    )

                    # Application des effets
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

                    if defenseur["vie"] <= 0:
                        log += f"\n🏆 **{attaquant['nom']} remporte le combat par KO !**"
                        await ctx.send(log)
                        return

                    log += "\n"

            # Fin des 5 tours : gagnant par PV restant
            gagnant = p1 if p1["vie"] > p2["vie"] else p2
            log += f"__🧾 Résumé final__\n{format_etat_ligne(p1)}\n{format_etat_ligne(p2)}\n\n"
            log += f"🏁 **Fin du combat.**\n🏆 **{gagnant['nom']} l'emporte par avantage de vie !**"
            await ctx.send(log)

        except FileNotFoundError:
            await ctx.send("❌ Fichier `bleach_personnages.json` introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Une erreur est survenue : {e}")


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CombatCommand(bot)
    for command in cog.get_commands():
        command.category = "Bleach"
    await bot.add_cog(cog)
    print("✅ Cog chargé : CombatCommand (catégorie = Bleach)")
