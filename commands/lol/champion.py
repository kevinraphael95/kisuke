# ────────────────────────────────────────────────────────────────────────────────
# 📌 champion_api.py — Commande interactive !champion
# Objectif : Consulter passif, sorts, build, runes et conseils d’un champion LoL
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# 📦 Imports nécessaires
import discord
from discord.ext import commands
from discord.ui import View, Select
import aiohttp

# 📂 API URLs
DD_VERSION = "13.6.1"
CHAMPIONS_LIST_URL = f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/data/en_US/champion.json"
CHAMPION_DATA_URL = lambda key: f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/data/en_US/champion/{key}.json"
UGG_API_URL = "https://u.gg/api/v1/champion-rankings/{champ}/ranks/overall"

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données champions via Data Dragon
# ────────────────────────────────────────────────────────────────────────────────
async def fetch_json(url):
    async with aiohttp.ClientSession() as s:
        async with s.get(url) as r:
            return await r.json()

class ChampData:
    champions = {}

    @classmethod
    async def load_list(cls):
        if not cls.champions:
            data = await fetch_json(CHAMPIONS_LIST_URL)
            cls.champions = data["data"]

    @classmethod
    async def load_champ(cls, key):
        data = await fetch_json(CHAMPION_DATA_URL(key))
        return data["data"][key]

    @classmethod
    async def load_ugg(cls, key):
        async with aiohttp.ClientSession() as s:
            async with s.get(UGG_API_URL.format(champ=key.lower())) as r:
                if r.status == 200:
                    return (await r.json())[0]
                return {}

# 🎛️ UI — Étape 1 : Sélection du champion
class ChampionSelectView(View):
    def __init__(self, bot):
        super().__init__(timeout=120)
        self.bot = bot
        self.champs = []
        self.add_item(ChampionSelect(self))

class ChampionSelect(Select):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(placeholder="Sélectionne un champion", options=[])
    async def on_ready(self):
        await ChampData.load_list()
        self.options = [discord.SelectOption(label=k, value=k) for k in sorted(ChampData.champions.keys())][:25]
    async def callback(self, interaction):
        champ = self.values[0]
        champ_data = await ChampData.load_champ(champ)
        champ_ugg = await ChampData.load_ugg(champ)
        view = PageSelectView(self.parent.bot, champ_data, champ_ugg)
        await interaction.response.edit_message(content=f"**{champ} sélectionné !** Choisis la page :", view=view, embed=None)

# 🎛️ UI — Étape 2 : Choix de la page d'infos
class PageSelectView(View):
    def __init__(self, bot, champ_data, champ_ugg):
        super().__init__(timeout=120)
        self.bot = bot
        self.champ_data = champ_data
        self.champ_ugg = champ_ugg
        self.add_item(PageSelect(self))

class PageSelect(Select):
    def __init__(self, parent):
        self.parent = parent
        opts = ["Passif", "Sorts", "Build", "Runes", "Conseils"]
        self.options = [discord.SelectOption(label=o, value=o.lower()) for o in opts]
        super().__init__(placeholder="Choisis une page", options=self.options)
    async def callback(self, interaction):
        data = self.parent.champ_data
        ugg = self.parent.champ_ugg
        page = self.values[0]
        embed = discord.Embed(title=f"{data['name']} — {page.capitalize()}", color=discord.Color.blue())
        if page == "passif":
            p = data["passive"]
            embed.set_thumbnail(url=f"https://ddragon.leagueoflegends.com/cdn/{DD_VERSION}/img/passive/{p['image']['full']}")
            embed.add_field(name=p["name"], value=p["description"], inline=False)
        elif page == "sorts":
            for spell in data["spells"]:
                embed.add_field(name=spell["name"], value=spell["description"], inline=False)
        elif page == "build":
            items = ugg.get("coreItems", [])
            embed.description = "\n".join(f"• {i}" for i in items) or "N/A"
        elif page == "runes":
            runes = ugg.get("runes", [])
            embed.description = "\n".join(f"• {r}" for r in runes) or "N/A"
        else:  # conseils
            tips = ugg.get("notes", []) or ["Pas de conseils disponibles."]
            embed.description = "\n".join(f"• {t}" for t in tips)
        await interaction.response.edit_message(embed=embed, view=self.parent)

# 🧠 Cog principal
class ChampionAPI(commands.Cog):
    """
    Commande !champion — Infos dynamiques sur un champion LoL
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="champion", help="Affiche passif, sorts, build, runes et conseils d'un champion LoL.")
    async def champion(self, ctx: commands.Context):
        try:
            view = ChampionSelectView(self.bot)
            await ChampData.load_list()
            await ctx.send("Sélectionne un champion :", view=view)
        except Exception as e:
            print(f"[ERREUR !champion] {e}")
            await ctx.send("❌ Une erreur est survenue lors de la récupération des données.")

# 🔌 Setup du Cog
async def setup(bot: commands.Bot):
    cog = ChampionAPI(bot)
    for cmd in cog.get_commands():
        if not hasattr(cmd, "category"):
            cmd.category = "LoL"
    await bot.add_cog(cog)
