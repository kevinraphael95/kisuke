# ────────────────────────────────────────────────────────────────────────────────
# 📌 course_voiture.py — Mini-jeu de course avec virages et pentes réalistes
# Objectif : Course animée entre voitures selon leurs stats
# Catégorie : Voiture
# Accès : Tous
# Cooldown : 0 (désactivé pour tests)
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random
import asyncio
from utils.discord_utils import safe_send, safe_edit
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Bouton de participation à la course
# ────────────────────────────────────────────────────────────────────────────────
class JoinRaceButton(Button):
    def __init__(self, race):
        super().__init__(label="🚗 Rejoindre la course", style=discord.ButtonStyle.green)
        self.race = race

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        try:
            res = supabase.table("voitures_users").select("*").eq("user_id", user_id).execute()
            user_data = res.data[0] if res.data else None
        except Exception as e:
            print(f"[SUPABASE ERR get user] {e}")
            return await interaction.response.send_message("⚠️ Erreur base de données.", ephemeral=True)

        if not user_data or not user_data.get("voiture_choisie"):
            user_data = {"voiture_choisie": "Ferrari Test"}

        voiture_choisie = user_data["voiture_choisie"]
        try:
            car_res = supabase.table("voitures_data").select("*").eq("nom", voiture_choisie).execute()
            car_data = car_res.data[0] if car_res.data else None
        except Exception as e:
            print(f"[SUPABASE ERR get car] {e}")
            car_data = None

        if not car_data:
            stats = {"vitesse_max": 220, "acceleration_0_100": 5.0, "maniabilite": 70, "poids": 1300}
        else:
            stats = car_data.get("stats", {"vitesse_max": 220, "acceleration_0_100": 5.0, "maniabilite": 70, "poids": 1300})

        # Ajout du joueur
        if user_id not in [p["user_id"] for p in self.race["participants"]]:
            if not self.race["available_emojis"]:
                return await interaction.response.send_message("❌ Course pleine.", ephemeral=True)
            emoji = self.race["available_emojis"].pop(0)
            self.race["participants"].append({
                "user_id": user_id,
                "username": interaction.user.display_name,
                "voiture": voiture_choisie,
                "stats": stats,
                "emoji": emoji,
                "position": 0,
                "is_bot": False
            })

        embed = self.generate_embed()
        await interaction.response.edit_message(embed=embed, view=self.view)

        # Démarrage auto si 4 joueurs
        if len(self.race["participants"]) >= 4:
            for child in self.view.children:
                child.disabled = True
            await interaction.edit_original_response(view=None)
            asyncio.create_task(self.start_race(interaction.channel))

    def generate_embed(self):
        embed = discord.Embed(
            title="🏁 Course en préparation",
            description=f"Hôte : **{self.race.get('host', 'inconnu')}** — Clique sur 🚗 pour participer !",
            color=discord.Color.blue()
        )
        participants = "\n".join(f"{p['emoji']} {p['username']} — {p['voiture']}" for p in self.race["participants"]) or "Aucun participant pour l’instant..."
        embed.add_field(name="Participants", value=participants, inline=False)
        embed.set_footer(text="Max 4 participants — la course démarre automatiquement.")
        return embed

    # ────────────────────────────────────────────────────────────────────────────
    # 🚦 Lancement de la course
    # ────────────────────────────────────────────────────────────────────────────
    async def start_race(self, channel: discord.abc.Messageable):
        # Ajouter des bots si nécessaire
        bot_pool = ["Bot-Kenzo", "Bot-Ryo", "Bot-Mika", "Bot-Luna"]
        while len(self.race["participants"]) < 4 and self.race["available_emojis"]:
            emoji = self.race["available_emojis"].pop(0)
            voiture = random.choice(["Ferrari F40", "McLaren F1", "Peugeot Oxia"])
            stats = {
                "vitesse_max": random.randint(230, 360),
                "acceleration_0_100": random.uniform(2.5, 5.0),
                "maniabilite": random.randint(65, 90),
                "poids": random.randint(1100, 1600)
            }
            self.race["participants"].append({
                "user_id": f"bot_{emoji}",
                "username": bot_pool.pop(0) if bot_pool else f"Bot{random.randint(1,99)}",
                "voiture": voiture,
                "stats": stats,
                "emoji": emoji,
                "position": 0,
                "is_bot": True
            })

        # Génération du circuit
        self.race["track"] = self.generate_track()
        msg = await safe_send(channel, "🏎️ **La course commence !** 🚦")
        await asyncio.sleep(2)
        await self.run_race(channel, msg)

    # ────────────────────────────────────────────────────────────────────────────
    # 🛣️ Génération du circuit
    # ────────────────────────────────────────────────────────────────────────────
    def generate_track(self):
        base_length = 25
        track = []
        specials = ["~", "~~", "⬆️", "⬇️"]
        num_special = random.randint(2, 4)

        while len(track) < base_length:
            if num_special > 0 and random.random() < 0.25 and (not track or track[-1] == "─"):
                track.append(random.choice(specials))
                num_special -= 1
                track.append("─")  # toujours un segment droit après un spécial
            else:
                track.append("─")

        return track[:base_length]

    # ────────────────────────────────────────────────────────────────────────────
    # 🏎️ Simulation de la course
    # ────────────────────────────────────────────────────────────────────────────
    async def run_race(self, channel, message):
        track = self.race["track"]
        track_length = len(track)
        finished = False
        winner = None

        for p in self.race["participants"]:
            p["position"] = 0

        while not finished:
            await asyncio.sleep(1.1)
            for p in self.race["participants"]:
                pos = min(int(p["position"]), track_length - 1)
                segment = track[pos]
                avance = self.calculate_advance(p["stats"], segment)
                p["position"] += avance
                if p["position"] >= track_length and not winner:
                    p["position"] = track_length
                    winner = p
                    finished = True

            track_text = self.render_track(self.race["participants"], track)
            classement = sorted(self.race["participants"], key=lambda x: -x["position"])
            leaderboard = "\n".join(f"{i+1}. {p['emoji']} {p['username']} ({p['voiture']})" for i, p in enumerate(classement))
            await safe_edit(message, f"🏎️ **Course en cours...**\n{track_text}\n\n**Classement provisoire :**\n{leaderboard}")

        await safe_edit(message, f"🏁 **Course terminée !**\nLe gagnant est 🏆 **{winner['emoji']} {winner['username']}** avec sa **{winner['voiture']}** ! 🎉")

    # ────────────────────────────────────────────────────────────────────────────
    # ⚙️ Calcul de l’avancée
    # ────────────────────────────────────────────────────────────────────────────
    def calculate_advance(self, stats, segment):
        base = stats["vitesse_max"]
        accel = stats["acceleration_0_100"]
        maniab = stats["maniabilite"]
        poids = stats["poids"]

        # Influence du segment
        if segment == "~":
            modif = 0.85  # petit virage
        elif segment == "~~":
            modif = 0.7   # grand virage
        elif segment == "⬆️":
            modif = 0.8   # montée
        elif segment == "⬇️":
            modif = 1.25  # descente
        else:
            modif = 1.0   # ligne droite

        # Calcul réaliste
        perf = (base / 280) * (12 / accel) * (maniab / 100) * (1200 / poids)
        avance = perf * modif * random.uniform(0.9, 1.1)
        return max(0.8, round(avance, 2))

    # ────────────────────────────────────────────────────────────────────────────
    # 🏁 Affichage de la piste
    # ────────────────────────────────────────────────────────────────────────────
    def render_track(self, participants, track):
        lines = []
        for p in participants:
            pos = min(int(p["position"]), len(track) - 1)
            route = "".join(track[:pos]) + "🚗" + "".join(track[pos+1:]) + " |🏁"
            lines.append(f"{p['emoji']} {route}")
        return "\n".join(lines)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CourseVoiture(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="course_voiture", description="Lance une course réaliste avec virages et pentes.")
    async def slash_course_voiture(self, interaction: discord.Interaction):
        race = {"host": interaction.user.display_name, "participants": [], "available_emojis": ["🇦", "🇧", "🇨", "🇩"]}
        view = View(timeout=60)
        button = JoinRaceButton(race)
        view.add_item(button)
        await interaction.response.send_message(embed=button.generate_embed(), view=view)

    @commands.command(name="course_voiture", aliases=["vcourse"])
    async def prefix_course_voiture(self, ctx):
        race = {"host": ctx.author.display_name, "participants": [], "available_emojis": ["🇦", "🇧", "🇨", "🇩"]}
        view = View(timeout=60)
        button = JoinRaceButton(race)
        view.add_item(button)
        await safe_send(ctx.channel, embed=button.generate_embed(), view=view)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CourseVoiture(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Voiture"
    await bot.add_cog(cog)
