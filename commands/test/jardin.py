# ────────────────────────────────────────────────────────────────────────────────
# 📌 jardin.py — Commande interactive /jardin et !jardin
# Objectif : Chaque utilisateur a un jardin persistant avec des fleurs
# Catégorie : Jeu
# Accès : Tout le monde
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import os
import random
import datetime
from utils.discord_utils import safe_send, safe_respond
from supabase import create_client, Client

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Connexion Supabase
# ────────────────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "gardens"

# ────────────────────────────────────────────────────────────────────────────────
# 🌱 Constantes du jeu
# ────────────────────────────────────────────────────────────────────────────────
DEFAULT_GRID = [
    "🌱🌱🌱🌱🌱🌱🌱🌱",
    "🌱🌱🌱🌱🌱🌱🌱🌱",
    "🌱🌱🌱🌱🌱🌱🌱🌱",
]
DEFAULT_INVENTORY = {
    "tulipes": 0,
    "roses": 0,
    "jacinthes": 0,
    "hibiscus": 0,
    "paquerettes": 0,
    "tournesols": 0,
}

FLEUR_EMOJIS = {
    "tulipes": "🌷",
    "roses": "🌹",
    "jacinthes": "🪻",
    "hibiscus": "🌺",
    "paquerettes": "🌼",
    "tournesols": "🌻"
}
FLEUR_LIST = list(FLEUR_EMOJIS.items())

FERTILIZE_COOLDOWN = datetime.timedelta(minutes=10)
FERTILIZE_PROBABILITY = 0.39

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
async def get_or_create_garden(user_id: int, username: str):
    res = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).execute()
    if res.data:
        return res.data[0]

    new_garden = {
        "user_id": user_id,
        "username": username,
        "garden_grid": DEFAULT_GRID.copy(),
        "inventory": DEFAULT_INVENTORY.copy(),
        "argent": 0,
        "armee": "",
        "last_fertilize": None
    }
    supabase.table(TABLE_NAME).insert(new_garden).execute()
    return new_garden

def build_garden_embed(garden: dict, viewer_id: int) -> discord.Embed:
    lines = garden["garden_grid"]
    inv_dict = garden["inventory"]
    inv = " / ".join(f"{FLEUR_EMOJIS[f]}{inv_dict.get(f, 0)}" for f in FLEUR_EMOJIS)

    cd_str = "✅ Disponible"
    if garden.get("last_fertilize"):
        try:
            last_dt = datetime.datetime.fromisoformat(garden["last_fertilize"])
            remain = last_dt + FERTILIZE_COOLDOWN - datetime.datetime.utcnow()
            if remain.total_seconds() > 0:
                total_seconds = int(remain.total_seconds())
                minutes, seconds = divmod(total_seconds, 60)
                hours, minutes = divmod(minutes, 60)
                cd_str = f"⏳ {hours}h {minutes}m {seconds}s"
        except Exception as e:
            print(f"[ERREUR parse last_fertilize] {e}")

    embed = discord.Embed(
        title=f"🏡 Jardin de {garden['username']}",
        description="\n".join(lines),
        color=discord.Color.green()
    )
    embed.add_field(
        name="Infos",
        value=f"Fleurs possédées : {inv}\n"
              f"Armée : {garden['armee'] or '—'} | Argent : {garden['argent']}💰\n"
              f"Cooldown engrais : {cd_str}",
        inline=False
    )
    return embed

def pousser_fleurs(lines: list[str]) -> list[str]:
    new_lines = []
    for line in lines:
        chars = []
        for c in line:
            if c == "🌱" and random.random() < FERTILIZE_PROBABILITY:
                _, emoji = random.choice(FLEUR_LIST)
                chars.append(emoji)
            else:
                chars.append(c)
        new_lines.append("".join(chars))
    return new_lines

def couper_fleurs(lines: list[str], garden: dict) -> tuple[list[str], dict]:
    new_lines = []
    inv = garden["inventory"]
    for line in lines:
        chars = []
        for c in line:
            for col, emoji in FLEUR_EMOJIS.items():
                if c == emoji:
                    inv[col] = inv.get(col, 0) + 1
                    c = "🌱"
            chars.append(c)
        new_lines.append("".join(chars))
    garden["inventory"] = inv
    return new_lines, garden

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Boutons d’action
# ────────────────────────────────────────────────────────────────────────────────
class JardinView(discord.ui.View):
    def __init__(self, garden: dict, user_id: int):
        super().__init__(timeout=120)
        self.garden = garden
        self.user_id = user_id
        self.update_buttons()  # Active/désactive Engrais dès le départ

    def update_buttons(self):
        """Active ou désactive le bouton Engrais selon le cooldown"""
        last = self.garden.get("last_fertilize")
        disabled = False
        if last:
            try:
                last_dt = datetime.datetime.fromisoformat(last)
                if datetime.datetime.utcnow() < last_dt + FERTILIZE_COOLDOWN:
                    disabled = True
            except Exception:
                pass

        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "Engrais":
                child.disabled = disabled

    async def update_garden_db(self):
        """Sauvegarde le jardin dans la base Supabase"""
        supabase.table(TABLE_NAME).update({
            "garden_grid": self.garden["garden_grid"],
            "inventory": self.garden["inventory"],
            "last_fertilize": self.garden["last_fertilize"],
            "argent": self.garden["argent"],
            "armee": self.garden["armee"]
        }).eq("user_id", self.user_id).execute()

    @discord.ui.button(label="Engrais", emoji="💩", style=discord.ButtonStyle.green)
    async def engrais(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        # Vérifie le cooldown
        last = self.garden.get("last_fertilize")
        if last:
            last_dt = datetime.datetime.fromisoformat(last)
            if datetime.datetime.utcnow() < last_dt + FERTILIZE_COOLDOWN:
                remain = last_dt + FERTILIZE_COOLDOWN - datetime.datetime.utcnow()
                total_seconds = int(remain.total_seconds())
                minutes, seconds = divmod(total_seconds, 60)
                hours, minutes = divmod(minutes, 60)
                return await interaction.response.send_message(
                    f"⏳ Tu dois attendre {hours}h {minutes}m {seconds}s avant d'utiliser de l'engrais !",
                    ephemeral=True
                )

        # Pousser les fleurs et mettre à jour le cooldown
        self.garden["garden_grid"] = pousser_fleurs(self.garden["garden_grid"])
        self.garden["last_fertilize"] = datetime.datetime.utcnow().isoformat()
        await self.update_garden_db()

        # Mettre à jour le bouton et l'embed sans recréer de nouvelle vue
        self.update_buttons()
        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=self)



    @discord.ui.button(label="Couper", emoji="✂️", style=discord.ButtonStyle.secondary)
    async def couper(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        new_lines, self.garden = couper_fleurs(self.garden["garden_grid"], self.garden)
        self.garden["garden_grid"] = new_lines
        await self.update_garden_db()

        # Actualiser la vue pour garder le cooldown
        view = JardinView(self.garden, self.user_id)
        view.update_buttons()
        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Alchimie", emoji="⚗️", style=discord.ButtonStyle.blurple)
    async def alchimie(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        embed = discord.Embed(
            title="⚗️ Alchimie",
            description="Fabriquer des potions grâce aux plantes de votre jardin.\n*(Attention : l'alchimie n'est pas encore ajoutée au bot)*",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="📖 Comment jouer",
            value=(
                "Vous commencez avec un alambic rempli d'eau qui vaut **0**.\n"
                "Ajouter des plantes de votre jardin change la valeur de votre mixture.\n"
                "Chaque potion a une valeur précise à atteindre pour pouvoir la créer.\n"
                "Une fois la valeur souhaitée atteinte, cliquez sur **Concocter**."
            ),
            inline=False
        )
        embed.add_field(
            name="🌿 Plantes",
            value="🌷+1  🌹+2  🪻x2  🌺x3  🌼-1  🌻-2",
            inline=False
        )
        embed.add_field(
            name="🧪 Potions",
            value=(
                "1. Potion de Mana 🔮 | Potion Anti Magie 🛡️ -1 \n"
                "2. Potion d’Agrandissement 📏 | Potion de Rétrécissement 📐 -2 \n"
                "3. Potion de Gel ❄️ | Potion Protection contre le Gel 🌡️ -3 \n"
                "4. Potion de Feu 🔥 | Potion Protection contre le Feu 🧯-4 \n"
                "5. Potion Foudre ⚡ | Potion de Protection contre la Foudre 🌩️ -5 \n"
                "6. Potion Acide 🧪 | Potion de Résistance à l’Acide 🥼 -6 \n"
                "7. Potion de Rajeunissement 🧴 | Potion de Nécromancie 🪦 -7 \n"
                "8. Potion de Force 💪 | Potion Somnifère 😴 -8 \n"
                "9. Potion de Lumière 💡 | Potion Explosion 💥 -9 \n"
                "10. Potion de Célérité 🏃‍♂️ | Potion Ralentissement 🐌 -10 \n"
                "11. Potion de Soin ❤️ | Potion de Poison 💀 -11 \n"
                "12. Potion de Vision 👁️ | Potion d’Invisibilité 👻 -12 \n"
                "13. Potion de Chance 🍀 | Potion de Pestilence ☣️ -13 \n"
                "14. Potion de Parfum 🌸 | Potion Charme 🪄 -14 \n"
                "15. Potion de Glisse ⛸️ | Potion Lévitation 🪁 -15 \n"
                "16. Potion de Dextérité 🤹 | Potion Peau de Pierre 🪨 -16"
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Jardin(commands.Cog):
    """Commande /jardin et !jardin — Voir son jardin"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="jardin", description="Affiche ton jardin ou celui d'un autre utilisateur 🌱")
    async def slash_jardin(self, interaction: discord.Interaction, user: discord.User = None):
        try:
            target = user or interaction.user
            garden = await get_or_create_garden(target.id, target.name)
            embed = build_garden_embed(garden, interaction.user.id)
            view = None if user else JardinView(garden, interaction.user.id)
            await safe_respond(interaction, embed=embed, view=view)
        except Exception as e:
            print(f"[ERREUR /jardin] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="jardin")
    async def prefix_jardin(self, ctx: commands.Context, user: discord.User = None):
        try:
            target = user or ctx.author
            garden = await get_or_create_garden(target.id, target.name)
            embed = build_garden_embed(garden, ctx.author.id)
            view = None if user else JardinView(garden, ctx.author.id)
            await safe_send(ctx.channel, embed=embed, view=view)
        except Exception as e:
            print(f"[ERREUR !jardin] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Jardin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
