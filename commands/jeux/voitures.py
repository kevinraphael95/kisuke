# ────────────────────────────────────────────────────────────────────────────────
# 📌 voitures_api.py — Commande /voiture, /garage et /infovoitures
# Objectif : Tirer des voitures aléatoires depuis une API, voir son garage, info sur voitures
# Catégorie : Jeux
# Accès : Tous
# Cooldown : Tirage 3 voitures toutes les 5 min, achat 1h, infovoitures 5s
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

from utils.discord_utils import safe_send
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Config
# ────────────────────────────────────────────────────────────────────────────────
COOLDOWN_VOITURE = 5 * 60       # 5 min
COOLDOWN_ACHETER = 60 * 60      # 1h
COOLDOWN_INFOS = 5              # 5 sec
API_URL = "https://www.carqueryapi.com/api/0.3/"
MAKES = ["peugeot", "renault", "citroen", "ferrari", "lamborghini", "porsche", "bmw", "audi"]

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
    Cog unifié : /voiture, /garage, /infovoitures
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
            "last_acheter": None,
            "last_infos": None
        }).execute()
        return await self.get_user(user)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Tirer n voitures aléatoires depuis l'API
    # ────────────────────────────────────────────────────────────────────────────
    def get_random_voitures(self, n=3):
        tirage = []
        while len(tirage) < n:
            make = random.choice(MAKES)
            params = {"cmd": "getTrims", "make": make, "sold_in_us": "1"}
            try:
                response = requests.get(API_URL, params=params, timeout=5)
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
            except:
                continue
        return tirage

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Tirage voitures
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
    # 🔹 /infovoitures — 5 voitures aléatoires ou une spécifique
    # ────────────────────────────────────────────────────────────────────────────
    async def send_info_voitures(self, channel, user, nom_voiture=None, n=5):
        last = user.get("last_infos")
        if last:
            last_dt = datetime.fromisoformat(last)
            if datetime.utcnow() - last_dt < timedelta(seconds=COOLDOWN_INFOS):
                remain = COOLDOWN_INFOS - (datetime.utcnow() - last_dt).seconds
                return await safe_send(channel, f"⏳ Attends encore {remain}s pour infos.")

        supabase.table("voitures_users").update({"last_infos": datetime.utcnow().isoformat()}).eq("user_id", str(user["user_id"])).execute()

        tirage = self.get_random_voitures(n)
        if nom_voiture:
            voiture = next((v for v in tirage if f"{v['make']} {v['model']}".lower() == nom_voiture.lower()), None)
            if not voiture:
                voiture = tirage[0]
            tirage = [voiture]

        embed = discord.Embed(
            title=f"🚗 Voitures aléatoires" if not nom_voiture else f"🚗 Détails de {tirage[0]['make']} {tirage[0]['model']}",
            color=discord.Color.blue()
        )
        for v in tirage:
            embed.add_field(
                name=f"{v['make']} {v['model']} ({v['year']})",
                value=f"Type: {v['body']}\nMoteur: {v['engine']}",
                inline=False
            )
            embed.set_image(url=v["image"])
        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commandes Slash
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="voiture", description="Tire 3 voitures aléatoires depuis l'API")
    async def slash_voiture(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = await self.get_user(interaction.user)
        await self.send_voiture_tirage(interaction.channel, user)
        await interaction.delete_original_response()

    @app_commands.command(name="garage", description="Voir ton garage")
    async def slash_garage(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = await self.get_user(interaction.user)
        await self.send_garage(interaction.channel, user)
        await interaction.delete_original_response()

    @app_commands.command(name="infovoitures", description="Afficher 5 voitures aléatoires ou une spécifique")
    @app_commands.describe(nom="Nom complet de la voiture (optionnel)")
    async def slash_infovoitures(self, interaction: discord.Interaction, nom: str = None):
        await interaction.response.defer(ephemeral=True)
        user = await self.get_user(interaction.user)
        await self.send_info_voitures(interaction.channel, user, nom_voiture=nom)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commandes Prefix
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="voiture", aliases=["v"])
    async def prefix_voiture(self, ctx: commands.Context):
        user = await self.get_user(ctx.author)
        await self.send_voiture_tirage(ctx.channel, user)

    @commands.command(name="garage")
    async def prefix_garage(self, ctx: commands.Context):
        user = await self.get_user(ctx.author)
        await self.send_garage(ctx.channel, user)

    @commands.command(name="infovoitures", aliases=["iv"])
    async def prefix_infovoitures(self, ctx: commands.Context, *, nom: str = None):
        user = await self.get_user(ctx.author)
        await self.send_info_voitures(ctx.channel, user, nom_voiture=nom)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = VoituresAPI(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
