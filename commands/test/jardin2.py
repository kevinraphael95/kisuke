import discord
from discord.ext import commands
import datetime
import random
import json
from utils.supabase_client import supabase
from utils.discord_utils import safe_send

# ─── Config jardin ───
with open("data/jardin_config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

DEFAULT_GRID = CONFIG["DEFAULT_GRID"]
FLEUR_EMOJIS = CONFIG["FLEUR_EMOJIS"]
FERTILIZE_PROBABILITY = CONFIG["FERTILIZE_PROBABILITY"]
FERTILIZE_COOLDOWN = datetime.timedelta(minutes=CONFIG["FERTILIZE_COOLDOWN_MINUTES"])
TABLE_NAME = "gardens"


# ─── Utilitaires ───
async def get_or_create_garden(user_id: int, username: str):
    res = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).execute()
    if res.data:
        return res.data[0]
    new_garden = {
        "user_id": user_id,
        "username": username,
        "garden_grid": DEFAULT_GRID.copy(),
        "inventory": {f: 0 for f in FLEUR_EMOJIS},
        "argent": 0,
        "armee": "",
        "last_fertilize": None
    }
    supabase.table(TABLE_NAME).insert(new_garden).execute()
    return new_garden


def pousser_fleurs(grid: list[str]) -> list[str]:
    new_grid = []
    for line in grid:
        new_line = ""
        for c in line:
            if c == "🌱" and random.random() < FERTILIZE_PROBABILITY:
                _, emoji = random.choice(list(FLEUR_EMOJIS.items()))
                new_line += emoji
            else:
                new_line += c
        new_grid.append(new_line)
    return new_grid


# ─── Vue Jardin2 ───
class Jardin2View(discord.ui.View):
    def __init__(self, garden: dict, user_id: int):
        super().__init__(timeout=300)
        self.garden = garden
        self.user_id = user_id

        # Crée les boutons du jardin (grille)
        for row_idx, row in enumerate(self.garden["garden_grid"]):
            for col_idx, cell in enumerate(row):
                self.add_item(FlowerButton(row_idx, col_idx, cell, self))

        # Ligne des commandes
        self.add_item(GlobalButton("💩", "engrais", self))
        self.add_item(GlobalButton("✂️", "couper", self))
        self.add_item(GlobalButton("🛍️", "inventaire", self))
        self.add_item(GlobalButton("⚗️", "alchimie", self))
        self.add_item(GlobalButton("💵", "magasin", self))

    async def refresh(self, interaction: discord.Interaction):
        """Recharge la vue + message"""
        new_view = Jardin2View(self.garden, self.user_id)
        await interaction.response.edit_message(
            content=self.format_garden(),
            view=new_view
        )

    def format_garden(self) -> str:
        grid_display = "\n".join(
            "[" + "][".join(row) + "]" for row in self.garden["garden_grid"]
        )
        return (
            f"**🏡 Jardin de {self.garden['username']}**\n"
            "💩:engrais, ✂️:couper, 🛍️:inventaire, ⚗️:alchimie, 💵:magasin\n"
            f"{grid_display}\n[💩][✂️][🛍️][⚗️][💵]"
        )


class FlowerButton(discord.ui.Button):
    def __init__(self, row: int, col: int, emoji: str, parent_view: Jardin2View):
        super().__init__(label=emoji, style=discord.ButtonStyle.secondary, row=row)
        self.row = row
        self.col = col
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        current = self.parent_view.garden["garden_grid"][self.row]
        char = current[self.col]

        # couper une fleur
        if char != "🌱":
            inv = self.parent_view.garden["inventory"]
            inv[char] = inv.get(char, 0) + 1
            row_list = list(current)
            row_list[self.col] = "🌱"
            self.parent_view.garden["garden_grid"][self.row] = "".join(row_list)

            # save
            supabase.table(TABLE_NAME).update({
                "garden_grid": self.parent_view.garden["garden_grid"],
                "inventory": self.parent_view.garden["inventory"]
            }).eq("user_id", self.parent_view.user_id).execute()

        await self.parent_view.refresh(interaction)


class GlobalButton(discord.ui.Button):
    def __init__(self, emoji: str, action: str, parent_view: Jardin2View):
        super().__init__(label=emoji, style=discord.ButtonStyle.green, row=4)
        self.action = action
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent_view.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        if self.action == "engrais":
            now = datetime.datetime.now(datetime.timezone.utc)
            last = self.parent_view.garden.get("last_fertilize")
            if last and now < datetime.datetime.fromisoformat(last) + FERTILIZE_COOLDOWN:
                return await interaction.response.send_message("⏳ Engrais en cooldown !", ephemeral=True)

            self.parent_view.garden["garden_grid"] = pousser_fleurs(self.parent_view.garden["garden_grid"])
            self.parent_view.garden["last_fertilize"] = now.isoformat()
            supabase.table(TABLE_NAME).update({
                "garden_grid": self.parent_view.garden["garden_grid"],
                "last_fertilize": self.parent_view.garden["last_fertilize"]
            }).eq("user_id", self.parent_view.user_id).execute()

        # TODO : inventaire, alchimie, magasin selon ton code existant

        await self.parent_view.refresh(interaction)


# ─── Cog ───
class Jardin2Cog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="jardin2")
    async def prefix_jardin2(self, ctx: commands.Context):
        garden = await get_or_create_garden(ctx.author.id, ctx.author.name)
        view = Jardin2View(garden, ctx.author.id)
        await safe_send(ctx.channel, content=view.format_garden(), view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Jardin2Cog(bot))
