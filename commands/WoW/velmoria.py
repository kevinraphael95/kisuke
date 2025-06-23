# ────────────────────────────────────────────────────────────────────────────────
# 📌 wow_velmoria.py — Commande interactive !velmoria
# Objectif : Afficher dynamiquement les infos du personnage Velmoria (WoW Way of Elendil)
# Catégorie : WoW
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Select
import aiohttp
from bs4 import BeautifulSoup
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Interface de sélection d’équipement
# ────────────────────────────────────────────────────────────────────────────────
class EquipementSelectView(View):
    def __init__(self, equipment: dict):
        super().__init__(timeout=60)
        self.equipment = equipment
        options = [discord.SelectOption(label=name, value=name) for name in equipment.keys()]
        self.add_item(EquipementSelect(self))

class EquipementSelect(Select):
    def __init__(self, parent: EquipementSelectView):
        super().__init__(
            placeholder="🧾 Sélectionne une pièce pour voir ses stats",
            min_values=1, max_values=1,
            options=[discord.SelectOption(label=n, value=n) for n in parent.equipment.keys()]
        )
        self.parent = parent

    async def callback(self, interaction: discord.Interaction):
        key = self.values[0]
        stats = self.parent.equipment[key]
        embed = discord.Embed(
            title=f"📦 {key}",
            description=f"```{stats}```",
            color=discord.Color.dark_green()
        )
        embed.set_footer(text="Velmoria – Way of Elendil")
        await interaction.response.edit_message(embed=embed, view=self.parent)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class VelmoriaCommand(commands.Cog):
    """
    Commande !velmoria — Infos du personnage Velmoria (WoW Way of Elendil)
    """

    ARMORY_URL = "https://way-of-elendil.fr/armory/character/988681-velmoria"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_character(self):
        async with aiohttp.ClientSession() as sess:
            async with sess.get(self.ARMORY_URL) as resp:
                text = await resp.text()
        soup = BeautifulSoup(text, "html.parser")
        # Exemple générique, adapter à la structure du site
        name = soup.select_one(".character-name").text.strip()
        lvl = soup.select_one(".character-level").text.strip()
        ilvl = soup.select_one(".character-itemlevel").text.strip()
        last = soup.select_one(".last-login").text.strip()

        equipment = {}
        for item in soup.select(".equipment-slot"):  # classe CSS hypothétique
            slot = item.select_one(".slot-name").text.strip()
            stats = "\n".join(li.text.strip() for li in item.select(".stat-line"))
            equipment[slot] = stats

        return {"name": name, "level": lvl, "ilvl": ilvl, "last": last, "equipment": equipment}

    @commands.command(
        name="velmoria",
        help="Affiche les infos de Velmoria (Way of Elendil).",
        description="Récupère en direct les infos du personnage WoW Velmoria."
    )
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def velmoria(self, ctx: commands.Context):
        try:
            data = await self.fetch_character()
            embed = discord.Embed(
                title=f"🔮 {data['name']} — Way of Elendil",
                url=self.ARMORY_URL,
                color=discord.Color.purple()
            )
            embed.add_field(name="👤 Niveau", value=data["level"], inline=True)
            embed.add_field(name="🏷️ iLvl", value=data["ilvl"], inline=True)
            embed.set_footer(text=f"Dernière connexion : {data['last']}")
            await ctx.send(embed=embed, view=EquipementSelectView(data["equipment"]))

        except Exception as e:
            print(f"[ERREUR velmoria] {e}")
            await ctx.send("❌ Impossible de récupérer les infos.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(VelmoriaCommand(bot))
