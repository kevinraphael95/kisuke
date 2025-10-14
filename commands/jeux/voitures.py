# ────────────────────────────────────────────────────────────────────────────────
# 📌 voitures_api.py — Commande interactive /voiture et !voiture
# Objectif : Tirer des voitures aléatoires depuis une API, pouvoir acheter via bouton et voir son garage
# Catégorie : Jeux
# Accès : Tous
# Cooldown : Tirage 3 voitures toutes les 5 min, achat 1h
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import random
from datetime import datetime, timedelta
import requests

from utils.discord_utils import safe_send, safe_edit, safe_respond
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Config
# ────────────────────────────────────────────────────────────────────────────────
COOLDOWN_VOITURE = 5 * 60       # 5 min
COOLDOWN_ACHETER = 60 * 60      # 1h
API_URL = "https://www.carqueryapi.com/api/0.3/"

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Bouton pour acheter une voiture
# ────────────────────────────────────────────────────────────────────────────────
class VoitureButton(Button):
    def __init__(self, voiture, user):
        super().__init__(label="Acheter 🚗", style=discord.ButtonStyle.green)
        self.voiture = voiture
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message("❌ Ce bouton n'est pas pour toi !", ephemeral=True)

        last = self.user.get("last_acheter")
        if last:
            last_dt = datetime.fromisoformat(last)
            if datetime.utcnow() - last_dt < timedelta(seconds=COOLDOWN_ACHETER):
                remain = COOLDOWN_ACHETER - (datetime.utcnow() - last_dt).seconds
                return await interaction.response.send_message(f"⏳ Attends encore {remain}s pour acheter.", ephemeral=True)

        voitures_user = self.user["voitures"]
        voitures_user.append(self.voiture)
        supabase.table("voitures_users").update({
            "voitures": voitures_user,
            "last_acheter": datetime.utcnow().isoformat()
        }).eq("user_id", str(self.user["user_id"])).execute()

        await interaction.response.edit_message(
            content=f"🎉 Tu as acheté **{self.voiture['make']} {self.voiture['model']} ({self.voiture['year']})** !",
            embed=None,
            view=None
        )

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class VoituresAPI(commands.Cog):
    """
    Commande /voiture et /garage et !voiture / !garage
    Tirage de voitures aléatoires depuis une API avec possibilité d'achat via bouton.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Récupération ou création d'un utilisateur Supabase
    # ────────────────────────────────────────────────────────────────────────────
    async def get_user(self, user: discord.User):
        res = supabase.table("voitures_users").select("*").eq("user_id", str(user.id)).execute()
        if res.data:
            return res.data[0]
        supabase.table("voitures_users").insert({
            "user_id": str(user.id),
            "username": str(user),
            "voitures": [],
            "last_voiture": None,
            "last_acheter": None
        }).execute()
        return await self.get_user(user)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Tirer des voitures aléatoires depuis l'API
    # ────────────────────────────────────────────────────────────────────────────
    def get_random_voitures(self, n=3):
        # Tirage de marques et modèles aléatoires
        makes = ["peugeot", "renault", "citroen", "ferrari", "lamborghini", "porsche", "bmw", "audi"]
        tirage = []
        while len(tirage) < n:
            make = random.choice(makes)
            params = {"cmd": "getTrims", "make": make, "sold_in_us": "1"}
            response = requests.get(API_URL, params=params)
            if response.status_code != 200:
                continue
            data = response.json().get("Trims", [])
            if not data:
                continue
            trim = random.choice(data)
            voiture = {
                "make": trim.get("model_make_id"),
                "model": trim.get("model_name"),
                "year": trim.get("model_year"),
                "body": trim.get("model_body"),
                "engine": trim.get("model_engine_type"),
                "image": f"https://loremflickr.com/320/240/car?random={random.randint(1,1000)}"
            }
            tirage.append(voiture)
        return tirage

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Envoyer le tirage
    # ────────────────────────────────────────────────────────────────────────────
    async def send_voiture_tirage(self, channel, user):
        last = user.get("last_voiture")
        if last:
            last_dt = datetime.fromisoformat(last)
            if datetime.utcnow() - last_dt < timedelta(seconds=COOLDOWN_VOITURE):
                remain = COOLDOWN_VOITURE - (datetime.utcnow() - last_dt).seconds
                return await safe_send(channel, f"⏳ Attends encore {remain}s pour tirer des voitures.")

        tirage = self.get_random_voitures()
        supabase.table("voitures_users").update({"last_voiture": datetime.utcnow().isoformat()}).eq("user_id", str(user["user_id"])).execute()

        for voiture in tirage:
            embed = discord.Embed(
                title=f"{voiture['make']} {voiture['model']} ({voiture['year']})",
                description=f"Type: {voiture['body']}\nMoteur: {voiture['engine']}",
                color=discord.Color.blue()
            )
            embed.set_image(url=voiture["image"])
            view = View()
            view.add_item(VoitureButton(voiture, user))
            await safe_send(channel, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Voir le garage
    # ────────────────────────────────────────────────────────────────────────────
    async def send_garage(self, channel, user):
        voitures_user = user["voitures"]
        if not voitures_user:
            return await safe_send(channel, "Ton garage est vide.")

        for v in voitures_user:
            embed = discord.Embed(
                title=f"{v['make']} {v['model']} ({v['year']})",
                description=f"Type: {v.get('body','?')}\nMoteur: {v.get('engine','?')}",
                color=discord.Color.green()
            )
            embed.set_image(url=v["image"])
            await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH Voiture
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="voiture", description="Tire 3 voitures aléatoires depuis l'API")
    async def slash_voiture(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = await self.get_user(interaction.user)
        await self.send_voiture_tirage(interaction.channel, user)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH Garage
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="garage", description="Voir ton garage")
    async def slash_garage(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = await self.get_user(interaction.user)
        await self.send_garage(interaction.channel, user)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX Voiture
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="voiture", aliases=["v"])
    async def prefix_voiture(self, ctx: commands.Context):
        user = await self.get_user(ctx.author)
        await self.send_voiture_tirage(ctx.channel, user)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX Garage
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="garage")
    async def prefix_garage(self, ctx: commands.Context):
        user = await self.get_user(ctx.author)
        await self.send_garage(ctx.channel, user)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = VoituresAPI(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
