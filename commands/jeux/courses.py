# ────────────────────────────────────────────────────────────────────────────────
# 📌 course_voiture.py — Mini-jeu de course de voitures avec stats dynamiques
# Objectif : Course animée basée sur les voitures choisies par les joueurs
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 0 (désactivé pour tests)
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random
import asyncio
from utils.discord_utils import safe_send, safe_respond, safe_edit
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Classe du bouton pour rejoindre la course
# ────────────────────────────────────────────────────────────────────────────────
class JoinRaceButton(Button):
    def __init__(self, race):
        super().__init__(label="🚗 Rejoindre la course", style=discord.ButtonStyle.green)
        self.race = race

    async def callback(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # Vérifier que l'utilisateur a une voiture choisie
        user_data = supabase.table("voitures_users").select("*").eq("user_id", user_id).execute().data
        if not user_data or not user_data[0].get("voiture_choisie"):
            return await interaction.response.send_message(
                "❌ Tu dois choisir une voiture avant de participer à une course !",
                ephemeral=True
            )

        voiture_choisie = user_data[0]["voiture_choisie"]

        # Récupérer les stats de la voiture
        voiture_data = supabase.table("voitures_data").select("*").eq("nom", voiture_choisie).execute().data
        if not voiture_data:
            return await interaction.response.send_message("⚠️ Impossible de trouver les stats de ta voiture.", ephemeral=True)

        stats = voiture_data[0]["stats"]

        # Ajouter le joueur
        if user_id not in [p["user_id"] for p in self.race["participants"]]:
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

        # Mettre à jour l'embed
        embed = self.generate_embed()
        await interaction.response.edit_message(embed=embed, view=self.view)

        # Lancer automatiquement quand 4 participants
        if len(self.race["participants"]) >= 4:
            for child in self.view.children:
                child.disabled = True
            await self.start_race(interaction.channel)

    def generate_embed(self):
        embed = discord.Embed(
            title="🏁 Course de voitures en préparation",
            description="Clique sur **🚗 Rejoindre la course** pour participer !",
            color=discord.Color.blue()
        )
        if self.race["participants"]:
            desc = "\n".join(f"{p['emoji']} {p['username']} — {p['voiture']}" for p in self.race["participants"])
        else:
            desc = "Aucun participant pour l’instant..."
        embed.add_field(name="Participants", value=desc, inline=False)
        return embed

    async def start_race(self, channel: discord.abc.Messageable):
        # Compléter avec des bots si nécessaire
        while len(self.race["participants"]) < 4 and self.race["available_emojis"]:
            emoji = self.race["available_emojis"].pop(0)
            bot_name = f"Bot{emoji}"
            voiture = random.choice(["Ferrari F40", "McLaren F1", "Peugeot Oxia"])
            stats = {
                "vitesse_max": random.randint(200, 360),
                "acceleration_0_100": random.uniform(2.5, 5.0),
                "maniabilite": random.randint(60, 90),
                "poids": random.randint(1100, 1600)
            }
            self.race["participants"].append({
                "user_id": f"bot_{emoji}",
                "username": bot_name,
                "voiture": voiture,
                "stats": stats,
                "emoji": emoji,
                "position": 0,
                "is_bot": True
            })

        await safe_send(channel, "🏎️ **La course commence !** Attachez vos ceintures...")
        await asyncio.sleep(2)
        await self.run_race(channel)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Animation de la course
    # ────────────────────────────────────────────────────────────────────────────
    async def run_race(self, channel: discord.abc.Messageable):
        track_length = 30
        message = await safe_send(channel, "🏁 Préparation du circuit...\n")
        finished = False
        winner = None

        while not finished:
            await asyncio.sleep(0.6)
            for p in self.race["participants"]:
                stats = p["stats"]
                avance = self.calculate_advance(stats)
                p["position"] += avance
                if p["position"] >= track_length:
                    p["position"] = track_length
                    if not winner:
                        winner = p
                        finished = True

            # Rendu du circuit
            track_text = self.render_track(self.race["participants"], track_length)
            await safe_edit(message, f"🏎️ **Course en cours...**\n{track_text}")

        await safe_edit(
            message,
            f"🏆 **Course terminée !**\nLe gagnant est **{winner['emoji']} {winner['username']}** avec sa **{winner['voiture']}** ! 🎉"
        )

    def render_track(self, participants, track_length):
        lines = []
        for p in participants:
            pos = min(int(p["position"]), track_length)
            track = f"{p['emoji']} " + "─" * pos + "🚗" + "─" * (track_length - pos) + " |🏁"
            lines.append(track)
        return "\n".join(lines)

    def calculate_advance(self, stats):
        base = stats.get("vitesse_max", 200)
        accel = stats.get("acceleration_0_100", 5)
        maniab = stats.get("maniabilite", 70)
        poids = stats.get("poids", 1300)

        # Formule d’avance simplifiée
        advance = (base / 100) * (10 / accel) * (maniab / 100) * (1200 / poids)
        return max(1, int(advance * random.uniform(0.8, 1.4)))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CourseVoiture(commands.Cog):
    """
    Commande /course_voiture et !course_voiture — Course entre joueurs selon leurs voitures.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="course_voiture",
        description="Lance une course animée entre 4 voitures selon leurs stats."
    )
    @app_commands.checks.cooldown(1, 0.0, key=lambda i: (i.user.id))  # Cooldown à 0 pour tests
    async def slash_course_voiture(self, interaction: discord.Interaction):
        race = {
            "host": interaction.user.display_name,
            "participants": [],
            "available_emojis": ["🇦", "🇧", "🇨", "🇩"]
        }
        view = View(timeout=60)
        button = JoinRaceButton(race)
        view.add_item(button)
        await safe_respond(interaction, embed=button.generate_embed(), view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="course_voiture", aliases=["vcourse"])
    async def prefix_course_voiture(self, ctx: commands.Context):
        race = {
            "host": ctx.author.display_name,
            "participants": [],
            "available_emojis": ["🇦", "🇧", "🇨", "🇩"]
        }
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
            command.category = "Jeux"
    await bot.add_cog(cog)
