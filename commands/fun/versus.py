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

    @commands.command(name="versus", help="Combat interactif entre deux joueurs avec des personnages Bleach.")
    async def versus(self, ctx):
        try:
            with open("data/bleach_personnages.json", "r", encoding="utf-8") as f:
                personnages = json.load(f)
        except FileNotFoundError:
            await ctx.send("❌ Fichier `bleach_personnages.json` introuvable.")
            return

        message_invite = await ctx.send("🧑‍🤝‍🧑 Deux joueurs doivent réagir avec ✋ pour rejoindre le combat.")
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

        p1_data, p2_data = random.sample(personnages, 2)
        p1_data["joueur"], p2_data["joueur"] = joueurs[0], joueurs[1]

        for perso in (p1_data, p2_data):
            perso["vie"] = 100
            perso["energie"] = 100
            perso["status"] = None
            perso["status_duree"] = 0
            for atk in perso["attaques"]:
                atk["utilisé"] = False

        await ctx.send(f"🎮 **{joueurs[0].mention} ({p1_data['nom']}) VS {joueurs[1].mention} ({p2_data['nom']}) !**")

        def format_etat(p):
            status = "✅ Aucun effet"
            if p["status"] == "gel":
                status = f"❄️ Gelé ({p['status_duree']} tour)"
            elif p["status"] == "confusion":
                status = f"💫 Confus ({p['status_duree']} tours)"
            elif p["status"] == "poison":
                status = f"☠️ Empoisonné ({p['status_duree']} tours)"
            return f"{p['nom']} ({p['joueur'].mention}) — ❤️ {p['vie']} PV | 🔋 {p['energie']} énergie | {status}"

        async def jouer_tour(joueur_data, adverse_data):
            if joueur_data["status"] == "gel":
                joueur_data["status_duree"] -= 1
                if joueur_data["status_duree"] <= 0:
                    joueur_data["status"] = None
                await ctx.send(f"❄️ {joueur_data['nom']} est gelé et ne peut pas agir.")
                return

            if joueur_data["status"] == "poison":
                joueur_data["vie"] -= 5
                joueur_data["status_duree"] -= 1
                if joueur_data["status_duree"] <= 0:
                    joueur_data["status"] = None
                await ctx.send(f"☠️ {joueur_data['nom']} perd 5 PV à cause du poison.")

            if joueur_data["status"] == "confusion":
                if random.random() < 0.4:
                    joueur_data["vie"] -= 10
                    joueur_data["status_duree"] -= 1
                    if joueur_data["status_duree"] <= 0:
                        joueur_data["status"] = None
                    await ctx.send(f"💫 {joueur_data['nom']} est confus et se blesse ! (-10 PV)")
                    return

            attaques_dispo = [
                a for a in joueur_data["attaques"]
                if a["cout"] <= joueur_data["energie"] and (a["type"] != "ultime" or not a["utilisé"])
            ]
            if not attaques_dispo:
                await ctx.send(f"💤 {joueur_data['nom']} n’a pas assez d’énergie pour attaquer.")
                return

            options = [SelectOption(label=a["nom"], description=f"{a['type']} - {a['cout']} énergie") for a in attaques_dispo]

            class AttaqueSelect(Select):
                def __init__(self):
                    super().__init__(placeholder="Choisissez une attaque", options=options)

                async def callback(self, interaction: Interaction):
                    if interaction.user != joueur_data["joueur"]:
                        await interaction.response.send_message("Ce n’est pas ton tour !", ephemeral=True)
                        return

                    attaque = next(a for a in attaques_dispo if a["nom"] == self.values[0])
                    if attaque["type"] == "ultime":
                        attaque["utilisé"] = True

                    esquive_chance = min(adverse_data["stats"]["mobilité"] / 40 + random.uniform(0, 0.2), 0.5)
                    esquive = random.random() < esquive_chance and adverse_data["energie"] >= 10

                    log = ""
                    if esquive:
                        cout = 50 if attaque["type"] == "ultime" else 10
                        adverse_data["energie"] -= cout
                        log += f"💨 {adverse_data['nom']} esquive l'attaque ! (-{cout} énergie)"
                    else:
                        base = attaque["degats"]
                        mod = joueur_data["stats"]["attaque"] + joueur_data["stats"]["force"] - adverse_data["stats"]["défense"]
                        total = base + max(0, mod)
                        if random.random() < min(0.1 + joueur_data["stats"]["force"] / 50, 0.4):
                            total = int(total * 1.5)
                            log += "💥 Coup critique !\n"
                        adverse_data["vie"] -= total
                        joueur_data["energie"] -= attaque["cout"]
                        log += f"{joueur_data['nom']} utilise **{attaque['nom']}** : {total} dégâts."

                        effet = attaque["effet"].lower()
                        if effet == "gel":
                            adverse_data["status"] = "gel"
                            adverse_data["status_duree"] = 1
                            log += f"\n❄️ {adverse_data['nom']} est gelé !"
                        elif effet == "confusion":
                            adverse_data["status"] = "confusion"
                            adverse_data["status_duree"] = 2
                            log += f"\n💫 {adverse_data['nom']} est confus !"
                        elif effet == "poison":
                            adverse_data["status"] = "poison"
                            adverse_data["status_duree"] = 3
                            log += f"\n☠️ {adverse_data['nom']} est empoisonné !"

                    await interaction.response.edit_message(content=log + "\n\n" + format_etat(joueur_data) + "\n" + format_etat(adverse_data), view=None)
                    interaction.client._next_turn.set_result(True)

            view = View()
            view.add_item(AttaqueSelect())
            await ctx.send(f"🎯 {joueur_data['joueur'].mention}, c'est à vous de jouer :", view=view)

            self.bot._next_turn = asyncio.get_event_loop().create_future()
            try:
                await asyncio.wait_for(self.bot._next_turn, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("⏰ Temps écoulé pour choisir une attaque.")

        combat_terminé = False
        tour = 1
        while not combat_terminé and tour <= 5:
            await ctx.send(f"🔁 **Tour {tour}**")
            await ctx.send(format_etat(p1_data) + "\n" + format_etat(p2_data))

            for j, adv in [(p1_data, p2_data), (p2_data, p1_data)]:
                if j["vie"] <= 0:
                    combat_terminé = True
                    break
                await jouer_tour(j, adv)
                if adv["vie"] <= 0:
                    await ctx.send(f"🏆 **{j['nom']} remporte le combat !**")
                    combat_terminé = True
                    break
            tour += 1

        if not combat_terminé:
            gagnant = p1_data if p1_data["vie"] > p2_data["vie"] else p2_data
            await ctx.send(f"🏁 Fin du combat après 5 tours. **{gagnant['nom']} gagne par PV restants !**")

# Chargement automatique
async def setup(bot):
    cog = VersusCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"
    await bot.add_cog(cog)
