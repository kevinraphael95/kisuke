# ────────────────────────────────────────────────────────────────────────────────
# 📌 voitures_json_full.py — Commande /voiture, /garage et /infovoitures avec JSON
# Objectif : Tirer des voitures depuis des fichiers JSON, voir son garage, info sur voitures
# Catégorie : Jeux
# Accès : Tous
# Cooldown : Tirage 3 voitures toutes les 5 min, achat 1h, infovoitures 5s
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button
import os
import json
from datetime import datetime, timedelta
import random

from utils.discord_utils import safe_send, safe_edit
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Config
# ────────────────────────────────────────────────────────────────────────────────
VOITURES_JSON_DIR = os.path.join("data", "voitures")
IMAGE_DEFAULT = os.path.join("data", "images", "image_par_defaut.jpg")
COOLDOWN_VOITURE = 5 * 60
COOLDOWN_ACHETER = 60 * 60
COOLDOWN_INFOS = 5

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Utilitaires JSON
# ────────────────────────────────────────────────────────────────────────────────
def load_voitures():
    voitures = {}
    if not os.path.exists(VOITURES_JSON_DIR):
        return voitures
    for f in os.listdir(VOITURES_JSON_DIR):
        if f.endswith(".json"):
            path = os.path.join(VOITURES_JSON_DIR, f)
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
                make = data.get("marque", "Inconnue")
                if make not in voitures:
                    voitures[make] = {}
                voitures[make][data["nom"]] = data
    return voitures

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Bouton pour acheter une voiture
# ────────────────────────────────────────────────────────────────────────────────
class VoitureButton(Button):
    def __init__(self, voiture, user):
        super().__init__(label="Acheter 🚗", style=discord.ButtonStyle.green)
        self.voiture = voiture
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user["user_id"]:
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
            content=f"🎉 Tu as acheté **{self.voiture['nom']}** !",
            embed=None,
            view=None
        )

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menus interactifs
# ────────────────────────────────────────────────────────────────────────────────
class FirstSelectView(View):
    def __init__(self, bot, data, user):
        super().__init__(timeout=120)
        self.bot = bot
        self.data = data
        self.user = user
        self.message = None
        self.add_item(FirstSelect(self))

class FirstSelect(Select):
    def __init__(self, parent_view: FirstSelectView):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=m, value=m) for m in self.parent_view.data.keys()]
        super().__init__(placeholder="Sélectionne une marque", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected = self.values[0]
        new_view = SecondSelectView(self.parent_view.bot, self.parent_view.data[selected], self.parent_view.user)
        new_view.message = interaction.message
        await safe_edit(interaction.message,
                        content=f"Marque sélectionnée : **{selected}**\nChoisis maintenant un modèle :",
                        embed=None, view=new_view)

class SecondSelectView(View):
    def __init__(self, bot, data, user):
        super().__init__(timeout=120)
        self.bot = bot
        self.data = data
        self.user = user
        self.message = None
        self.add_item(SecondSelect(self))

class SecondSelect(Select):
    def __init__(self, parent_view: SecondSelectView):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=m, value=m) for m in self.parent_view.data.keys()]
        super().__init__(placeholder="Sélectionne un modèle", options=options)

    async def callback(self, interaction: discord.Interaction):
        model = self.values[0]
        infos = self.parent_view.data[model]
        embed = discord.Embed(title=model, color=discord.Color.blue())
        stats = infos.get("stats", {})
        for k, v in stats.items():
            embed.add_field(name=k.capitalize(), value=str(v), inline=True)
        image = infos.get("image", IMAGE_DEFAULT)
        embed.set_image(url=image)
        view = View()
        view.add_item(VoitureButton(infos, self.parent_view.user))
        await safe_edit(interaction.message, content=None, embed=embed, view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class VoituresJSONFull(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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

    async def send_menu(self, channel, user):
        data = load_voitures()
        if not data:
            return await safe_send(channel, "❌ Impossible de charger les données.")
        view = FirstSelectView(self.bot, data, user)
        view.message = await safe_send(channel, "Choisis une marque :", view=view)

    async def send_garage(self, channel, user):
        voitures_user = user.get("voitures", [])
        if not voitures_user:
            return await safe_send(channel, "Ton garage est vide.")
        for v in voitures_user:
            embed = discord.Embed(title=v.get("nom", "?"), color=discord.Color.green())
            stats = v.get("stats", {})
            for k, val in stats.items():
                embed.add_field(name=k.capitalize(), value=str(val), inline=True)
            embed.set_image(url=v.get("image", IMAGE_DEFAULT))
            await safe_send(channel, embed=embed)

    async def send_info_voitures(self, channel, user, nom_voiture=None, n=5):
        data = load_voitures()
        all_voitures = [v for marques in data.values() for v in marques.values()]
        tirage = random.sample(all_voitures, min(n, len(all_voitures)))
        if nom_voiture:
            voiture = next((v for v in all_voitures if v["nom"].lower() == nom_voiture.lower()), None)
            if voiture:
                tirage = [voiture]
        for v in tirage:
            embed = discord.Embed(title=v.get("nom","?"), color=discord.Color.blue())
            stats = v.get("stats", {})
            for k, val in stats.items():
                embed.add_field(name=k.capitalize(), value=str(val), inline=True)
            embed.set_image(url=v.get("image", IMAGE_DEFAULT))
            await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # Commandes Slash
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="voiture", description="Choisis une voiture depuis le menu")
    async def slash_voiture(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = await self.get_user(interaction.user)
        await self.send_menu(interaction.channel, user)
        await interaction.delete_original_response()

    @app_commands.command(name="garage", description="Voir ton garage")
    async def slash_garage(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = await self.get_user(interaction.user)
        await self.send_garage(interaction.channel, user)
        await interaction.delete_original_response()

    @app_commands.command(name="infovoitures", description="Afficher des voitures")
    @app_commands.describe(nom="Nom complet de la voiture (optionnel)")
    async def slash_infovoitures(self, interaction: discord.Interaction, nom: str = None):
        await interaction.response.defer(ephemeral=True)
        user = await self.get_user(interaction.user)
        await self.send_info_voitures(interaction.channel, user, nom_voiture=nom)
        await interaction.delete_original_response()

    # ────────────────────────────────────────────────────────────────────────────
    # Commandes Prefix
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="voiture", aliases=["v"])
    async def prefix_voiture(self, ctx: commands.Context):
        user = await self.get_user(ctx.author)
        await self.send_menu(ctx.channel, user)

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
    cog = VoituresJSONFull(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
