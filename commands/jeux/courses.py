# ────────────────────────────────────────────────────────────────────────────────
# 📌 course_voitures.py — Mini-jeu de course à 4 voitures avec stats animées et bouton
# Objectif : Lancer une course animée avec voitures, virages et pentes
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 0 secondes pour test
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random, asyncio

from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Bouton pour rejoindre la course
# ────────────────────────────────────────────────────────────────────────────────
class JoinButton(Button):
    def __init__(self, race):
        super().__init__(label="Rejoindre 🚗", style=discord.ButtonStyle.green)
        self.race = race

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        # Stats fictives pour test
        voiture_stats = {"vitesse_max": 349,"acceleration_0_100":3.6,"maniabilite":85,"poids":1360}

        # Ajouter participant humain
        if user_id not in [p["user_id"] for p in self.race["participants"]]:
            self.race["participants"].append({
                "user_id": user_id,
                "username": interaction.user.display_name,
                "stats": voiture_stats,
                "is_bot": False,
                "emoji": self.race["available_emojis"].pop(0),
                "position": 0
            })
            await interaction.response.edit_message(embed=self.race_embed(), view=self.view)

        # Ajouter bots si nécessaire
        while len(self.race["participants"]) < 4:
            bot_name = f"Bot{len(self.race['participants'])+1}"
            bot_stats = {"vitesse_max": random.randint(300, 350),
                         "acceleration_0_100": random.uniform(3, 5),
                         "maniabilite": random.randint(70, 90),
                         "poids": random.randint(1300, 1500)}
            self.race["participants"].append({
                "user_id": f"bot{len(self.race['participants'])}",
                "username": bot_name,
                "stats": bot_stats,
                "is_bot": True,
                "emoji": self.race["available_emojis"].pop(0),
                "position": 0
            })

        # Lancer la course si 4 participants
        if len(self.race["participants"]) >= 4:
            for child in self.view.children:
                child.disabled = True
            await self.start_race(interaction)

    def race_embed(self):
        embed = discord.Embed(
            title="🏁 Course en préparation !",
            description="Clique sur **Rejoindre 🚗** pour participer !",
            color=discord.Color.blue()
        )
        participants_text = "\n".join(
            f"{p['emoji']} {p['username']}" for p in self.race["participants"]
        )
        embed.add_field(name="Participants", value=participants_text or "Aucun participant", inline=False)
        return embed

    async def start_race(self, interaction: discord.Interaction):
        await safe_edit(interaction.message, content="🏎️ La course commence !", embed=None, view=None)
        await self.race_animation(interaction.channel)

    async def race_animation(self, channel):
        track_template = ["─", "=", "↗️", "─", "==", "↘️", "─", "=", "↗️", "─", "==", "↘️", "🏁"]
        max_distance = len(track_template) * 5  # distance totale
        finished = False

        while not finished:
            await asyncio.sleep(1)
            finished = False
            lines = []
            for p in self.race["participants"]:
                section = track_template[p["position"] % len(track_template)]
                advance = self.calculate_advance(p["stats"], section)
                p["position"] += advance
                if p["position"] >= max_distance:
                    p["position"] = max_distance
                    finished = True
                # ligne de piste
                repeated_track = [track_template[(i + p["position"]) % len(track_template)] for i in range(len(track_template))]
                line = f"{p['emoji']} " + "".join(repeated_track)
                lines.append(line)

            embed = discord.Embed(title="🏁 Course en cours !", description="\n".join(lines), color=discord.Color.green())
            msg = await safe_send(channel, embed=embed)
            await asyncio.sleep(0.5)
            await msg.delete()

        winner = max(self.race["participants"], key=lambda x: x["position"])
        await safe_send(channel, f"🏆 **Course terminée !** Le gagnant est **{winner['username']}** !")

    def calculate_advance(self, stats, section):
        base = stats.get("vitesse_max", 200)
        accel = stats.get("acceleration_0_100", 5)
        maniab = stats.get("maniabilite", 50)
        poids = stats.get("poids", 1300)

        advance = int((base/100) * (10/accel) * (maniab/100) * (1200/poids))
        if section == "↗️":
            advance = max(1, int(advance * 0.5))
        elif section == "↘️":
            advance = max(1, int(advance * 1.2))
        elif section == "=":
            advance = max(1, int(advance * 0.8))
        else:
            advance = max(1, advance)
        return advance

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CourseVoitures(commands.Cog):
    """
    Commande /course et !course — Mini-jeu de course à 4 voitures
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_races = {}
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="course", description="Lance une course à 4 voitures !")
    @app_commands.checks.cooldown(1, 0, key=lambda i: i.user.id)  # cooldown 0 pour test
    async def slash_course(self, interaction: discord.Interaction):
        race = {
            "host": interaction.user.display_name,
            "participants": [],
            "available_emojis": ["🇦","🇧","🇨","🇩"]
        }
        view = View(timeout=60)
        button = JoinButton(race)
        view.add_item(button)
        race["view"] = view
        await safe_send(interaction.channel, embed=button.race_embed(), view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="course")
    @commands.cooldown(1, 0, commands.BucketType.user)  # cooldown 0 pour test
    async def prefix_course(self, ctx: commands.Context):
        await self.slash_course(ctx)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CourseVoitures(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
