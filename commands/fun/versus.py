# ─────────────────────────────────────────────────────────────
# ⚔️ COMMANDE "VERSUS" — DUEL DE PERSONNAGES BLEACH EN INTERACTIF
# ─────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import SelectOption, Interaction
from discord.ui import Select, View
import json
import random
import asyncio

class VersusCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="versus",
        help="⚔️ Duel entre deux joueurs avec des personnages aléatoires de Bleach."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def versus(self, ctx):
        # Chargement des personnages
        try:
            with open("data/bleach_personnages.json", "r", encoding="utf-8") as f:
                personnages = json.load(f)
        except FileNotFoundError:
            await ctx.send("❌ Fichier `bleach_personnages.json` introuvable.")
            return

        # Phase d’invitation
        message_invite = await ctx.send("✋ Deux joueurs doivent réagir pour rejoindre le combat.")
        await message_invite.add_reaction("✋")

        joueurs = []

        def check_reaction(reaction, user):
            return (
                reaction.message.id == message_invite.id and
                str(reaction.emoji) == "✋" and
                user != self.bot.user and
                user not in joueurs
            )

        while len(joueurs) < 2:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check_reaction)
                joueurs.append(user)
                await ctx.send(f"✅ {user.mention} a rejoint le combat.")
            except asyncio.TimeoutError:
                await ctx.send("⏰ Temps écoulé. Le combat est annulé.")
                return

        # Attribution des personnages
        p1, p2 = random.sample(personnages, 2)
        p1["joueur"], p2["joueur"] = joueurs[0], joueurs[1]

        for perso in (p1, p2):
            perso.update({
                "vie": 100,
                "energie": 100,
                "status": None,
                "status_duree": 0
            })
            for atk in perso["attaques"]:
                atk["utilisé"] = False

        await ctx.send(f"🎮 **{p1['joueur'].mention} ({p1['nom']}) VS {p2['joueur'].mention} ({p2['nom']}) !**")

        def format_etat(p):
            status_dict = {
                "gel": f"❄️ Gelé ({p['status_duree']} tour)",
                "confusion": f"💫 Confus ({p['status_duree']} tours)",
                "poison": f"☠️ Empoisonné ({p['status_duree']} tours)"
            }
            status = status_dict.get(p["status"], "✅ Aucun effet")
            return f"**{p['nom']}** ({p['joueur'].mention})\n❤️ PV: {p['vie']} | 🔋 Énergie: {p['energie']} | {status}"

        async def jouer_tour(joueur, adversaire):
            # Gestion des effets de statut
            if joueur["status"] == "gel":
                joueur["status_duree"] -= 1
                if joueur["status_duree"] <= 0: joueur["status"] = None
                await ctx.send(f"❄️ {joueur['nom']} est gelé et ne peut pas agir ce tour.")
                return

            if joueur["status"] == "poison":
                joueur["vie"] -= 5
                joueur["status_duree"] -= 1
                if joueur["status_duree"] <= 0: joueur["status"] = None
                await ctx.send(f"☠️ {joueur['nom']} perd 5 PV à cause du poison.")

            if joueur["status"] == "confusion":
                if random.random() < 0.4:
                    joueur["vie"] -= 10
                    joueur["status_duree"] -= 1
                    if joueur["status_duree"] <= 0: joueur["status"] = None
                    await ctx.send(f"💫 {joueur['nom']} est confus et se blesse lui-même ! (-10 PV)")
                    return

            # Filtrage des attaques disponibles
            attaques_dispo = [
                a for a in joueur["attaques"]
                if a["cout"] <= joueur["energie"] and (a["type"] != "ultime" or not a["utilisé"])
            ]
            if not attaques_dispo:
                await ctx.send(f"💤 {joueur['nom']} n’a pas assez d’énergie pour attaquer.")
                return

            # Création des options pour le menu
            options = [SelectOption(label=a["nom"], description=f"{a['type']} — {a['cout']} énergie") for a in attaques_dispo]

            class ChoixAttaque(Select):
                def __init__(self):
                    super().__init__(placeholder="⚔️ Choisis ton attaque :", options=options)

                async def callback(self, interaction: Interaction):
                    if interaction.user != joueur["joueur"]:
                        await interaction.response.send_message("🚫 Ce n’est pas ton tour !", ephemeral=True)
                        return

                    attaque = next(a for a in attaques_dispo if a["nom"] == self.values[0])
                    if attaque["type"] == "ultime":
                        attaque["utilisé"] = True

                    esquive_chance = min(adversaire["stats"]["mobilité"] / 40 + random.uniform(0, 0.2), 0.5)
                    esquive = random.random() < esquive_chance and adversaire["energie"] >= 10

                    log = f"🎯 **{joueur['nom']}** utilise **{attaque['nom']}** !\n"
                    if esquive:
                        cout = 50 if attaque["type"] == "ultime" else 10
                        adversaire["energie"] -= cout
                        log += f"💨 Mais **{adversaire['nom']}** esquive l’attaque ! (-{cout} énergie)"
                    else:
                        mod = joueur["stats"]["attaque"] + joueur["stats"]["force"] - adversaire["stats"]["défense"]
                        degats = attaque["degats"] + max(0, mod)
                        if random.random() < min(0.1 + joueur["stats"]["force"] / 50, 0.4):
                            degats = int(degats * 1.5)
                            log += "💥 Coup critique !\n"
                        adversaire["vie"] -= degats
                        joueur["energie"] -= attaque["cout"]
                        log += f"🔻 Dégâts infligés : **{degats}**\n"

                        # Effets spéciaux
                        effet = attaque["effet"].lower()
                        effets = {
                            "gel": "❄️ est gelé",
                            "confusion": "💫 est confus",
                            "poison": "☠️ est empoisonné"
                        }
                        if effet in effets:
                            adversaire["status"] = effet
                            adversaire["status_duree"] = {"gel":1, "confusion":2, "poison":3}[effet]
                            log += f"{effets[effet]} !"

                    await interaction.response.edit_message(
                        content=log + "\n\n" + format_etat(joueur) + "\n" + format_etat(adversaire),
                        view=None
                    )
                    interaction.client._next_turn.set_result(True)

            view = View()
            view.add_item(ChoixAttaque())
            await ctx.send(f"🎮 {joueur['joueur'].mention}, fais ton choix :", view=view)

            self.bot._next_turn = asyncio.get_event_loop().create_future()
            try:
                await asyncio.wait_for(self.bot._next_turn, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("⏰ Temps écoulé. Tour perdu.")

        # 🌀 Boucle de combat
        tour = 1
        combat_terminé = False
        while not combat_terminé and tour <= 5:
            await ctx.send(f"🔄 **Tour {tour}**")
            await ctx.send(format_etat(p1) + "\n" + format_etat(p2))

            for j, adv in [(p1, p2), (p2, p1)]:
                if j["vie"] <= 0:
                    combat_terminé = True
                    break
                await jouer_tour(j, adv)
                if adv["vie"] <= 0:
                    await ctx.send(f"🏆 **{j['nom']}** remporte le combat !")
                    combat_terminé = True
                    break
            tour += 1

        # Fin du combat
        if not combat_terminé:
            gagnant = p1 if p1["vie"] > p2["vie"] else p2
            await ctx.send(f"🏁 **Combat terminé après 5 tours.**\n🏅 **{gagnant['nom']}** gagne par PV restants !")

# Chargement auto
async def setup(bot):
    cog = VersusCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
