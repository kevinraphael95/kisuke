# ────────────────────────────────────────────────────────────────────────────────
# 📌 course_voitures.py — Mini-jeu de course à 4 voitures avec stats animées
# Objectif : Lancer une course animée avec voitures, virages et pentes
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 24h / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CarRace(commands.Cog):
    """
    Commande /course et !course — Mini-jeu animé de course de voitures avec stats
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.track_template = ["─", "=", "↗️", "─", "==", "↘️", "─", "=", "↗️", "─", "==", "↘️", "🏁"]
        self.emojis = ["🇦", "🇧", "🇨", "🇩"]

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne pour calculer l’avance selon stats
    # ────────────────────────────────────────────────────────────────────────────
    def calculate_advance(self, stats, section):
        base = stats.get("vitesse_max", 200)
        accel = stats.get("acceleration_0_100", 5)
        maniab = stats.get("maniabilite", 50)
        poids = stats.get("poids", 1300)

        advance = int((base/100) * (10/accel) * (maniab/100) * (1200/poids))
        if section == "↗️":  # montée
            advance = max(1, int(advance * 0.5))
        elif section == "↘️":  # descente
            advance = max(1, int(advance * 1.2))
        elif section == "=":  # ligne longue
            advance = max(1, int(advance * 0.8))
        else:
            advance = max(1, advance)
        return advance

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne pour créer l'affichage de la piste
    # ────────────────────────────────────────────────────────────────────────────
    def render_track(self, participants):
        lines = []
        track_length = len(self.track_template)
        for p in participants:
            pos = p["position"]
            repeated_track = []
            # effet piste continue
            for i in range(track_length):
                repeated_track.append(self.track_template[(i + pos) % track_length])
            line = f"{p['emoji']} " + "".join(repeated_track)
            lines.append(line)
        return "\n".join(lines)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne pour lancer la course
    # ────────────────────────────────────────────────────────────────────────────
    async def run_race(self, channel):
        # Participants fictifs pour test
        participants = [
            {"username": "Joueur", "stats": {"vitesse_max": 349,"acceleration_0_100":3.6,"maniabilite":85,"poids":1360}, "position": 0, "emoji": self.emojis[0]},
            {"username": "Bot1", "stats": {"vitesse_max": 320,"acceleration_0_100":4,"maniabilite":80,"poids":1400}, "position": 0, "emoji": self.emojis[1]},
            {"username": "Bot2", "stats": {"vitesse_max": 300,"acceleration_0_100":4.5,"maniabilite":75,"poids":1350}, "position": 0, "emoji": self.emojis[2]},
            {"username": "Bot3", "stats": {"vitesse_max": 310,"acceleration_0_100":4.2,"maniabilite":78,"poids":1320}, "position": 0, "emoji": self.emojis[3]},
        ]

        message = await safe_send(channel, "🏁 La course commence !\n")
        finished = False

        while not finished:
            await asyncio.sleep(1)
            finished = False
            for p in participants:
                section = self.track_template[p["position"] % len(self.track_template)]
                p["position"] += self.calculate_advance(p["stats"], section)
                if p["position"] >= len(self.track_template) * 5:  # distance totale
                    p["position"] = len(self.track_template) * 5
                    finished = True

            track_text = self.render_track(participants)
            await safe_edit(message, f"🏁 **Course en cours :**\n{track_text}")

        winner = max(participants, key=lambda x: x["position"])
        await safe_edit(message, f"🏆 **Course terminée !** Le gagnant est **{winner['username']}** !")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="course",
        description="Lance une course animée de voitures avec stats."
    )
    @app_commands.checks.cooldown(1, 86400, key=lambda i: i.user.id)  # 24h cooldown
    async def slash_course(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self.run_race(interaction.channel)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /course] {e}")
            await safe_send(interaction.channel, "❌ Une erreur est survenue.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="course")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def prefix_course(self, ctx: commands.Context):
        await self.run_race(ctx.channel)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CarRace(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
