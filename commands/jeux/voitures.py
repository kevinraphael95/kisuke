# ────────────────────────────────────────────────────────────────────────────────
# 📌 voitures.py — Commande interactive /voiture et !voiture
# Objectif : Tirer des voitures aléatoires, pouvoir acheter via bouton et voir son garage
# Catégorie : Jeux
# Accès : Tous
# Cooldown : Tirage 1 voiture toutes les 5 min, achat 1h
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import json, os, random
from datetime import datetime, timedelta

from utils.discord_utils import safe_send
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON des voitures
# ────────────────────────────────────────────────────────────────────────────────
DATA_PATH = "data/voitures"
COOLDOWN_VOITURE = 5 * 60       # 5 min
COOLDOWN_ACHETER = 60 * 60      # 1h

def load_voitures():
    voitures = []
    for file in os.listdir(DATA_PATH):
        if file.endswith(".json"):
            with open(os.path.join(DATA_PATH, file), "r", encoding="utf-8") as f:
                voitures.append(json.load(f))
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
        if str(interaction.user.id) != str(self.user["user_id"]):
            return await interaction.response.send_message("❌ Ce bouton n'est pas pour toi !", ephemeral=True)

        res = supabase.table("voitures_users").select("*").eq("user_id", str(self.user["user_id"])).execute()
        if not res.data:
            return await interaction.response.send_message("⚠️ Erreur : utilisateur introuvable.", ephemeral=True)
        user_data = res.data[0]

        # Cooldown achat
        last = user_data.get("last_acheter")
        if last:
            last_dt = datetime.fromisoformat(last)
            delta = timedelta(seconds=COOLDOWN_ACHETER) - (datetime.utcnow() - last_dt)
            if delta.total_seconds() > 0:
                h, rem = divmod(int(delta.total_seconds()), 3600)
                m, s = divmod(rem, 60)
                return await interaction.response.send_message(
                    f"⏳ Attends encore {h}h {m}m {s}s avant d’acheter une autre voiture.", ephemeral=True
                )

        voitures_user = set(user_data.get("voitures", []))  # set pour éviter les doublons
        voitures_user.add(self.voiture["nom"])
        voitures_user = sorted(voitures_user)  # ordre alphabétique

        supabase.table("voitures_users").update({
            "voitures": voitures_user,
            "last_acheter": datetime.utcnow().isoformat()
        }).eq("user_id", str(user_data["user_id"])).execute()

        self.disabled = True
        await interaction.response.edit_message(
            content=f"🎉 Tu as acheté **{self.voiture['nom']}** ({self.voiture['rarete']}) !",
            embed=None,
            view=None
        )

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Voitures(commands.Cog):
    """
    Commande /voiture et /garage et !voiture / !garage
    Tirage de voitures aléatoires avec possibilité d'achat via bouton.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voitures = load_voitures()

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
    # 🔹 Tirer 1 voiture aléatoire
    # ────────────────────────────────────────────────────────────────────────────
    async def send_voiture_tirage(self, channel, user):
        last = user.get("last_voiture")
        if last:
            last_dt = datetime.fromisoformat(last)
            delta = timedelta(seconds=COOLDOWN_VOITURE) - (datetime.utcnow() - last_dt)
            if delta.total_seconds() > 0:
                h, rem = divmod(int(delta.total_seconds()), 3600)
                m, s = divmod(rem, 60)
                return await safe_send(channel, f"⏳ Attends encore {h}h {m}m {s}s pour tirer une voiture.")

        # Exclure les voitures déjà possédées
        owned_names = set(user.get("voitures", []))
        available = [v for v in self.voitures if v["nom"] not in owned_names]
        if not available:
            return await safe_send(channel, "🎉 Tu possèdes déjà toutes les voitures !")

        voiture = random.choice(available)
        supabase.table("voitures_users").update({"last_voiture": datetime.utcnow().isoformat()}).eq("user_id", str(user["user_id"])).execute()

        embed = discord.Embed(
            title=f"{voiture['nom']} ({voiture['rarete']})",
            description=voiture.get("description", ""),
            color=discord.Color.blue()
        )
        embed.set_image(url=voiture["image"])
        view = View()
        view.add_item(VoitureButton(voiture, user))
        await safe_send(channel, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Voir le garage (pagination 20 par page)
    # ────────────────────────────────────────────────────────────────────────────
    async def send_garage(self, channel, user):
        voitures_user = sorted(user.get("voitures", []))  # ordre alphabétique
        if not voitures_user:
            return await safe_send(channel, "🚗 Ton garage est vide.")

        pages = [voitures_user[i:i + 20] for i in range(0, len(voitures_user), 20)]

        class GaragePaginator(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)
                self.current_page = 0

            async def update_message(self, interaction=None):
                page_voitures = pages[self.current_page]
                embed = discord.Embed(
                    title=f"🚗 Garage de {len(voitures_user)} voitures",
                    color=discord.Color.green()
                )
                description = "\n".join(f"{v}" for v in page_voitures)
                embed.description = description
                embed.set_footer(text=f"Page {self.current_page + 1}/{len(pages)}")

                if interaction:
                    await interaction.response.edit_message(embed=embed, view=self)
                else:
                    await safe_send(channel, embed=embed, view=self)

            @discord.ui.button(label="◀️", style=discord.ButtonStyle.grey)
            async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.current_page > 0:
                    self.current_page -= 1
                    await self.update_message(interaction)

            @discord.ui.button(label="▶️", style=discord.ButtonStyle.grey)
            async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.current_page < len(pages) - 1:
                    self.current_page += 1
                    await self.update_message(interaction)

        paginator = GaragePaginator()
        await paginator.update_message()

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH Voiture
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="voiture", description="Tire une voiture aléatoire")
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
    cog = Voitures(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
