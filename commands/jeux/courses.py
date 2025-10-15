# ────────────────────────────────────────────────────────────────────────────────
# 📌 course_voitures.py — Mini-jeu de course à 4 voitures avec stats complètes
# Objectif : Lancer une course animée avec voitures, virages et pentes
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 24h / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random, asyncio, datetime

from utils.discord_utils import safe_send, safe_edit
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Bouton pour rejoindre la course
# ────────────────────────────────────────────────────────────────────────────────
class JoinButton(Button):
    def __init__(self, race):
        super().__init__(label="Rejoindre 🚗", style=discord.ButtonStyle.green)
        self.race = race

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        # Vérifier voiture choisie
        user_data = supabase.table("voitures_users").select("*").eq("user_id", user_id).execute().data[0]
        voiture_choisie = user_data.get("voiture_choisie")
        if not voiture_choisie:
            return await interaction.response.send_message("❌ Tu dois choisir une voiture avant de rejoindre !", ephemeral=True)

        # Stats de la voiture
        voitures_data = supabase.table("voitures_data").select("*").eq("nom", voiture_choisie).execute().data
        if voitures_data:
            voiture_stats = voitures_data[0]["stats"]
        else:
            voiture_stats = {"vitesse_max": 100, "acceleration_0_100": 5, "maniabilite": 50, "poids": 1200}

        # Ajouter participant humain
        if user_id not in [p["user_id"] for p in self.race["participants"]]:
            self.race["participants"].append({
                "user_id": user_id,
                "username": interaction.user.display_name,
                "voiture": voiture_choisie,
                "stats": voiture_stats,
                "is_bot": False,
                "emoji": self.race["available_emojis"].pop(0),
                "position": 0
            })
            await interaction.response.edit_message(embed=self.race_embed(), view=self.view)

        # Ajouter bots si nécessaire
        while len(self.race["participants"]) < 4:
            bot_name = f"Bot{len(self.race['participants'])+1}"
            bot_voiture = random.choice(["Peugeot Oxia", "Ferrari F40", "McLaren F1"])
            bot_stats = {
                "vitesse_max": random.randint(200, 350),
                "acceleration_0_100": random.uniform(3, 6),
                "maniabilite": random.randint(60, 90),
                "poids": random.randint(1200, 1600)
            }
            self.race["participants"].append({
                "user_id": f"bot{len(self.race['participants'])}",
                "username": bot_name,
                "voiture": bot_voiture,
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
            f"{p['emoji']} {p['username']} — 🚗 {p['voiture']}" for p in self.race["participants"]
        )
        embed.add_field(name="Participants", value=participants_text or "Aucun participant", inline=False)
        return embed

    async def start_race(self, interaction: discord.Interaction):
        await safe_edit(interaction.message, content="🏎️ La course commence !", embed=None, view=None)
        await self.race_animation(interaction.channel)

    async def race_animation(self, channel):
        track_template = ["─", "=", "↗️", "─", "=", "↘️", "─", "==", "↗️", "↘️", "🏁"]
        max_pos = len(track_template) - 1
        finished = False

        while not finished:
            finished = False
            lines = []
            for p in self.race["participants"]:
                avance = self.calculate_advance(p, track_template[p["position"]])
                p["position"] += avance
                if p["position"] >= max_pos:
                    p["position"] = max_pos
                    finished = True
                line = f"{p['emoji']} 🚗 {p['voiture']} " + "".join(track_template[:p["position"]]) + "🏁"
                lines.append(line)

            embed = discord.Embed(title="🏁 Course en cours !", description="\n".join(lines), color=discord.Color.green())
            msg = await safe_send(channel, embed=embed)
            await asyncio.sleep(1)
            await msg.delete()

        winner = max(self.race["participants"], key=lambda x: x["position"])
        await safe_send(channel, f"🏆 **Course terminée !** Le gagnant est {winner['username']} avec {winner['voiture']} !")

    def calculate_advance(self, participant, track_section):
        stats = participant["stats"]
        base = stats.get("vitesse_max", 100)
        accel = stats.get("acceleration_0_100", 5)
        maniab = stats.get("maniabilite", 50)
        poids = stats.get("poids", 1200)

        # Influence stats sur l'avance
        speed_factor = base / 100
        accel_factor = (10 / accel)
        maniab_factor = maniab / 100
        poids_factor = 1200 / poids
        advance = int(speed_factor * accel_factor * maniab_factor * poids_factor)

        # Modifier selon la section de piste
        if track_section == "↗️":
            advance = max(1, int(advance * 0.5))
        elif track_section == "↘️":
            advance = max(1, int(advance * 1.2))
        elif track_section == "=":
            advance = max(1, int(advance * 0.8))
        else:
            advance = max(1, advance)

        return advance

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CourseVoitures(commands.Cog):
    """
    Commande /course et !course — Mini-jeu de course à 4 voitures avec stats
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_races = {}
        self.bot = bot

    @app_commands.command(name="course", description="Lance une course à 4 voitures !")
    async def slash_course(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        # TODO: Vérifier cooldown 24h via Supabase
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

    @commands.command(name="course")
    async def prefix_course(self, ctx: commands.Context):
        await self.slash_course(ctx)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CourseVoitures(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
