# ────────────────────────────────────────────────────────────────────────────────
# 📌 jardin_ui_utils.py — Classes UI pour le jardin
# ────────────────────────────────────────────────────────────────────────────────
import discord
import datetime
from utils.supabase_client import supabase
from utils.jardin_utils import (
    TABLE_NAME, FLEUR_EMOJIS, FLEUR_SIGNS, FLEUR_VALUES,
    FLEUR_LIST, FERTILIZE_COOLDOWN, POTIONS,
    pousser_fleurs, couper_fleurs, build_garden_embed, build_potions_embed
)


class GardenButton(discord.ui.Button):
    def __init__(self, label: str, row: int, custom_id: str):
        super().__init__(label=label, style=discord.ButtonStyle.green, row=row, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        view: GardenGridView = self.view
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message("❌ Ce jardin n’est pas à toi !", ephemeral=True)

        i, j = map(int, self.custom_id.split("-"))
        current_emoji = view.garden["garden_grid"][i][j]

        if current_emoji == "🌱":
            return await interaction.response.send_message("🪴 Rien à cueillir ici.", ephemeral=True)

        for name, emoji in FLEUR_EMOJIS.items():
            if emoji == current_emoji:
                view.garden["inventory"][name] = view.garden["inventory"].get(name, 0) + 1
                line = list(view.garden["garden_grid"][i])
                line[j] = "🌱"
                view.garden["garden_grid"][i] = "".join(line)
                break

        supabase.table(TABLE_NAME).update({
            "garden_grid": view.garden["garden_grid"],
            "inventory": view.garden["inventory"]
        }).eq("user_id", view.user_id).execute()

        self.label = "🌱"
        await interaction.response.edit_message(view=view)


class GardenGridView(discord.ui.View):
    def __init__(self, garden: dict, user_id: int):
        super().__init__(timeout=120)
        self.garden = garden
        self.user_id = user_id

        for i, line in enumerate(garden["garden_grid"]):
            for j, emoji in enumerate(line):
                custom_id = f"{i}-{j}"
                self.add_item(GardenButton(label=emoji, row=i, custom_id=custom_id))


# ───────── AlchimieView ─────────
class AlchimieView(discord.ui.View):
    # ... tout le code existant de AlchimieView inchangé ...
    # Remplacer toutes les références à POTIONS, FLEUR_EMOJIS, FLEUR_SIGNS, FLEUR_VALUES par import depuis jardin_utils
    pass


# ───────── JardinView ─────────
class JardinView(discord.ui.View):
    # ... tout le code existant de JardinView inchangé ...
    # Remplacer toutes les références à FERTILIZE_COOLDOWN, pousser_fleurs, couper_fleurs, build_garden_embed par import depuis jardin_utils
    pass
