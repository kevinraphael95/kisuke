# ────────────────────────────────────────────────────────────────────────────────
# 📌 jardin_ui_utils.py — Views et Buttons pour le jardin et l’alchimie
# Objectif : Contient GardenGridView, JardinView et AlchimieView
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
import datetime
from utils.jardin_utils import (
    FLEUR_EMOJIS, FLEUR_SIGNS, FLEUR_VALUES, FLEUR_LIST,
    POTIONS, FERTILIZE_COOLDOWN, pousser_fleurs, couper_fleurs,
    build_garden_embed
)
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 🌱 GardenGridView et GardenButton
# ────────────────────────────────────────────────────────────────────────────────
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

        # Chercher le nom de la fleur
        for name, emoji in FLEUR_EMOJIS.items():
            if emoji == current_emoji:
                view.garden["inventory"][name] = view.garden["inventory"].get(name, 0) + 1
                line = list(view.garden["garden_grid"][i])
                line[j] = "🌱"
                view.garden["garden_grid"][i] = "".join(line)
                break

        # Mise à jour dans la base
        supabase.table("gardens").update({
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

        # Créer les boutons pour chaque case du jardin
        for i, line in enumerate(garden["garden_grid"]):
            for j, emoji in enumerate(line):
                custom_id = f"{i}-{j}"
                self.add_item(GardenButton(label=emoji, row=i, custom_id=custom_id))


# ────────────────────────────────────────────────────────────────────────────────
# ⚗️ Alchimie interactive
# ────────────────────────────────────────────────────────────────────────────────
class AlchimieView(discord.ui.View):
    def __init__(self, garden: dict, user_id: int, timeout=180):
        super().__init__(timeout=timeout)
        self.garden = garden
        self.user_id = user_id
        self.original_inventory = garden["inventory"].copy()
        self.temp_inventory = garden["inventory"].copy()
        self.value = 0
        self.selected_flowers = []

    def build_embed(self):
        fleurs_grouped = {"+" : [], "×" : [], "-" : []}
        for f in FLEUR_EMOJIS:
            sign = FLEUR_SIGNS[f]
            val = FLEUR_VALUES[f]
            fleurs_grouped[sign].append(f"{FLEUR_EMOJIS[f]}{sign}{val}")
        fleurs = "  ".join(" ".join(fleurs_grouped[s]) for s in ("+", "×", "-"))
        chosen = " ".join(FLEUR_EMOJIS[f] for f in self.selected_flowers) if self.selected_flowers else "—"

        import discord
        return discord.Embed(
            title="⚗️ Alchimie",
            description=f"Valeurs de fleurs : {fleurs}\n\n⚗️ {chosen}\nValeur : **{self.value}**",
            color=discord.Color.purple()
        )

    async def update_message(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    def use_flower(self, flower: str) -> bool:
        if self.temp_inventory.get(flower, 0) <= 0:
            return False
        self.temp_inventory[flower] -= 1
        self.selected_flowers.append(flower)

        sign = FLEUR_SIGNS[flower]
        val = FLEUR_VALUES[flower]
        if sign == "+":
            self.value += val
        elif sign == "-":
            self.value -= val
        elif sign == "×":
            self.value = self.value * val if self.value != 0 else val
        return True

    # ───────── Boutons fleurs ─────────
    @discord.ui.button(label="🌷", style=discord.ButtonStyle.green)
    async def add_tulipe(self, interaction, button):
        if not self.use_flower("tulipes"):
            return await interaction.response.send_message("❌ Tu n’as plus de 🌷 !", ephemeral=True)
        await self.update_message(interaction)

    @discord.ui.button(label="🌹", style=discord.ButtonStyle.green)
    async def add_rose(self, interaction, button):
        if not self.use_flower("roses"):
            return await interaction.response.send_message("❌ Tu n’as plus de 🌹 !", ephemeral=True)
        await self.update_message(interaction)

    @discord.ui.button(label="🪻", style=discord.ButtonStyle.green)
    async def add_jacinthe(self, interaction, button):
        if not self.use_flower("jacinthes"):
            return await interaction.response.send_message("❌ Tu n’as plus de 🪻 !", ephemeral=True)
        await self.update_message(interaction)

    @discord.ui.button(label="🌺", style=discord.ButtonStyle.green)
    async def add_hibiscus(self, interaction, button):
        if not self.use_flower("hibiscus"):
            return await interaction.response.send_message("❌ Tu n’as plus de 🌺 !", ephemeral=True)
        await self.update_message(interaction)

    @discord.ui.button(label="🌼", style=discord.ButtonStyle.green)
    async def add_paquerette(self, interaction, button):
        if not self.use_flower("paquerettes"):
            return await interaction.response.send_message("❌ Tu n’as plus de 🌼 !", ephemeral=True)
        await self.update_message(interaction)

    @discord.ui.button(label="🌻", style=discord.ButtonStyle.green)
    async def add_tournesol(self, interaction, button):
        if not self.use_flower("tournesols"):
            return await interaction.response.send_message("❌ Tu n’as plus de 🌻 !", ephemeral=True)
        await self.update_message(interaction)

    # ───────── Concocter & Reset ─────────
    @discord.ui.button(label="Concocter", emoji="⚗️", style=discord.ButtonStyle.blurple)
    async def concocter(self, interaction, button):
        potion = POTIONS.get(str(self.value))
        garden_update = {"inventory": self.temp_inventory.copy()}

        if potion:
            user_data = supabase.table("gardens").select("potions").eq("user_id", self.user_id).execute()
            potions_data = user_data.data[0]["potions"] if user_data.data and user_data.data[0].get("potions") else {}
            potions_data[potion] = potions_data.get(potion, 0) + 1
            garden_update["potions"] = dict(sorted(
                potions_data.items(),
                key=lambda x: next((int(v) for v, n in POTIONS.items() if n == x[0]), 0)
            ))
            await interaction.response.send_message(f"✨ Tu as créé : **{potion}** !", ephemeral=False)
        else:
            await interaction.response.send_message("💥 Ta mixture explose ! Rien obtenu...", ephemeral=False)

        supabase.table("gardens").update(garden_update).eq("user_id", self.user_id).execute()
        self.stop()

    @discord.ui.button(label="Reset", emoji="🔄", style=discord.ButtonStyle.red)
    async def reset(self, interaction, button):
        self.temp_inventory = self.original_inventory.copy()
        self.value = 0
        self.selected_flowers = []
        await self.update_message(interaction)

    async def interaction_check(self, interaction):
        return interaction.user.id == self.user_id


# ────────────────────────────────────────────────────────────────────────────────
# 🌱 JardinView — Boutons Jardin
# ────────────────────────────────────────────────────────────────────────────────
class JardinView(discord.ui.View):
    def __init__(self, garden: dict, user_id: int):
        super().__init__(timeout=120)
        self.garden = garden
        self.user_id = user_id

    def update_buttons(self):
        last = self.garden.get("last_fertilize")
        disabled = False
        if last:
            try:
                last_dt = datetime.datetime.fromisoformat(last)
                now = datetime.datetime.now(datetime.timezone.utc)
                if now < last_dt + FERTILIZE_COOLDOWN:
                    disabled = True
            except Exception:
                pass
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label == "Engrais":
                child.disabled = disabled

    async def update_garden_db(self):
        supabase.table("gardens").update({
            "garden_grid": self.garden["garden_grid"],
            "inventory": self.garden["inventory"],
            "last_fertilize": self.garden["last_fertilize"],
            "argent": self.garden["argent"],
            "armee": self.garden["armee"]
        }).eq("user_id", self.user_id).execute()

    @discord.ui.button(label="🪴 Voir la grille", style=discord.ButtonStyle.green)
    async def show_grid(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Affiche la grille interactive du jardin (clic sur les fleurs)."""
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n’est pas à toi !", ephemeral=True)

        from utils.jardin_ui_utils import GardenGridView  # éviter import circulaire
        grid_view = GardenGridView(self.garden, self.user_id)

        await interaction.response.edit_message(
            content="🌾 **Clique sur les fleurs pour les cueillir !**",
            embed=None,
            view=grid_view
    )
        
