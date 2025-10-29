# ────────────────────────────────────────────────────────────────────────────────
# 📌 devinepays.py — Jeu /devinepays et !devinepays : Devine le pays mystère
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp, random, math, unicodedata, asyncio, time
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
def normalize(text: str) -> str:
    if not text:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn').strip()

def haversine_km(coord1, coord2):
    R = 6371
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return int(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def compare_numeric(a, b):
    if a == b:
        return "🟩"
    diff = abs(a - b)
    ratio = diff / max(a, b)
    if ratio < 0.1:
        return "🟨"
    elif ratio < 0.4:
        return "🟧"
    else:
        return "🟥"

def color_text(condition: bool) -> str:
    return "🟩" if condition else "🟥"

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class DevinePays(commands.Cog):
    """
    Commande /devinepays et !devinepays — Devine un pays mystère !
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.countries = []
        self.games = {}

    async def cog_load(self):
        await self._load_countries()

    async def _load_countries(self):
        """Charge la liste des pays via l’API restcountries."""
        url = "https://restcountries.com/v3.1/all"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                data = await r.json()
        self.countries = [{
            "name": c["name"]["common"],
            "normalized": normalize(c["name"]["common"]),
            "population": c.get("population", 0),
            "area": c.get("area", 0),
            "continent": c.get("region", "Inconnu"),
            "languages": list(c.get("languages", {}).values()) if c.get("languages") else [],
            "currency": list(c.get("currencies", {}).keys())[0] if c.get("currencies") else "?",
            "latlng": c.get("latlng", [0, 0]),
            "capital": c.get("capital", ["?"])[0],
            "flag": c.get("flags", {}).get("png")
        } for c in data if "name" in c]
        print(f"[devinepays] {len(self.countries)} pays chargés.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="devinepays",
        description="Devine le pays mystère !"
    )
    @app_commands.describe(pays="Ton essai (ex: France, Brésil, Japon...)")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_devinepays(self, interaction: discord.Interaction, pays: str = None):
        await self._play(interaction, pays)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="devinepays")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_devinepays(self, ctx: commands.Context, *, pays: str = None):
        await self._play(ctx, pays)

    # ────────────────────────────────────────────────────────────────────────────
    # 🎮 Logique principale du jeu
    # ────────────────────────────────────────────────────────────────────────────
    async def _play(self, source, pays: str):
        """Gère le jeu pour slash et prefix"""
        # 🔸 Distinction interaction / message
        if isinstance(source, discord.Interaction):
            user = source.user
            channel = source.channel
        else:
            user = source.author
            channel = source.channel

        # 🔹 Si pas encore de partie, en lancer une
        if user.id not in self.games:
            secret = random.choice(self.countries)
            self.games[user.id] = {
                "secret": secret,
                "attempts": 0,
                "found": False
            }
            embed = discord.Embed(
                title="🌍 Nouveau jeu — Devine le pays mystère !",
                description="Entre un pays avec `/devinepays <nom>` ou `!devinepays <nom>`.\n\nBonne chance ! 🇺🇳",
                color=discord.Color.blurple()
            )
            await safe_respond(source, embed=embed)
            return

        # 🔹 Partie en cours
        game = self.games[user.id]
        secret = game["secret"]
        game["attempts"] += 1

        guess = next((c for c in self.countries if normalize(pays) == c["normalized"]), None)
        if not guess:
            await safe_respond(source, "❌ Ce pays n’existe pas ou n’est pas reconnu. Réessaie !", ephemeral=True)
            return

        # ✅ Si trouvé
        if guess["normalized"] == secret["normalized"]:
            game["found"] = True
            await safe_send(channel, f"🎉 Bravo {user.mention} ! Tu as trouvé le pays mystère **{secret['name']}** 🇺🇳 en {game['attempts']} essai(s) !")
            if secret["flag"]:
                flag_embed = discord.Embed(color=discord.Color.green())
                flag_embed.set_image(url=secret["flag"])
                await safe_send(channel, embed=flag_embed)
            del self.games[user.id]
            return

        # ❌ Comparaison
        dist = haversine_km(guess["latlng"], secret["latlng"])
        embed = discord.Embed(
            title=f"❌ Mauvais pays ({guess['name']})",
            description=f"Essai n°{game['attempts']} — Voici les comparaisons :",
            color=discord.Color.red()
        )
        embed.add_field(name="🌍 Continent", value=color_text(guess["continent"] == secret["continent"]) + f" {guess['continent']}", inline=False)
        embed.add_field(name="🗣️ Langue", value=color_text(any(lang in secret["languages"] for lang in guess["languages"])) + f" {', '.join(guess['languages']) or '—'}", inline=False)
        embed.add_field(name="💰 Monnaie", value=color_text(guess["currency"] == secret["currency"]) + f" {guess['currency']}", inline=False)
        embed.add_field(name="👥 Population", value=f"{compare_numeric(guess['population'], secret['population'])} {guess['population']:,}", inline=False)
        embed.add_field(name="📏 Superficie", value=f"{compare_numeric(guess['area'], secret['area'])} {guess['area']:,} km²", inline=False)
        embed.add_field(name="📍 Distance", value=f"{dist:,} km", inline=False)
        embed.set_footer(text=f"Essai #{game['attempts']} — Bonne chance {user.display_name} !")

        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🧹 Déchargement du Cog
    # ────────────────────────────────────────────────────────────────────────────
    async def cog_unload(self):
        self.games.clear()

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = DevinePays(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
