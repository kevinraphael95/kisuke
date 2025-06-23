# ──────────────────────────────────────────────────────────────
# 📁 WOW > Velmoria
# ──────────────────────────────────────────────────────────────

# 📦 IMPORTS
import discord
from discord.ext import commands
from discord.ui import View, Select
import aiohttp
from bs4 import BeautifulSoup

# ──────────────────────────────────────────────────────────────
# 🎛️ VIEW : Menu déroulant des équipements
# ──────────────────────────────────────────────────────────────
class EquipementSelectView(View):
    def __init__(self, equipment: dict):
        super().__init__(timeout=60)
        self.equipment = equipment
        self.add_item(EquipementSelect(self))


class EquipementSelect(Select):
    def __init__(self, parent: EquipementSelectView):
        options = [discord.SelectOption(label=name, value=name) for name in parent.equipment]
        super().__init__(
            placeholder="🧾 Sélectionne une pièce pour voir ses stats",
            min_values=1, max_values=1,
            options=options
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

# ──────────────────────────────────────────────────────────────
# 🔧 COG : VelmoriaCommand
# ──────────────────────────────────────────────────────────────
class VelmoriaCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ARMORY_URL = "https://way-of-elendil.fr/armory/character/988681-velmoria"

    async def fetch_character(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(self.ARMORY_URL) as resp:
                html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        try:
            name = soup.select_one(".character-name").text.strip()
            lvl = soup.select_one(".character-level").text.strip()
            ilvl = soup.select_one(".character-itemlevel").text.strip()
            last = soup.select_one(".last-login").text.strip()
        except AttributeError:
            raise ValueError("❌ Impossible de parser les infos du personnage.")

        equipment = {}
        for item in soup.select(".equipment-slot"):  # Adapter si nécessaire
            try:
                slot = item.select_one(".slot-name").text.strip()
                stats = "\n".join(li.text.strip() for li in item.select(".stat-line"))
                equipment[slot] = stats
            except:
                continue

        return {"name": name, "level": lvl, "ilvl": ilvl, "last": last, "equipment": equipment}

    # ──────────────────────────────────────────────────────────
    # 🔮 COMMANDE : !velmoria
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="velmoria",
        help="Affiche les infos de Velmoria (Way of Elendil)."
    )
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
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
            await ctx.send("❌ Impossible de récupérer les infos de Velmoria.")

    # 🏷️ Catégorisation personnalisée (pour système de !help custom)
    def cog_load(self):
        self.velmoria.category = "WoW"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(VelmoriaCommand(bot))
    print("✅ Cog chargé : VelmoriaCommand (catégorie = WoW)")
