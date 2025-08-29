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
from utils.discord_utils import safe_send, safe_respond
from utils.jardin_utils import (
    supabase, TABLE_NAME, DEFAULT_GRID, DEFAULT_INVENTORY,
    FLOWERS, FERTILIZE_CFG, POTIONS, FERTILIZE_COOLDOWN, FERTILIZE_PROBABILITY,
    FLEUR_EMOJIS, FLEUR_VALUES, FLEUR_SIGNS, FLEUR_LIST,
    get_or_create_garden, build_garden_embed, pousser_fleurs, couper_fleurs
)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Alchimie interactive
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

    def add_flower_buttons(self):
        for flower, emoji in FLEUR_EMOJIS.items():
            async def callback(interaction, f=flower):
                if not self.use_flower(f):
                    return await interaction.response.send_message(f"❌ Tu n’as plus de {FLEUR_EMOJIS[f]} !", ephemeral=True)
                await self.update_message(interaction)
            self.add_item(discord.ui.Button(label=emoji, style=discord.ButtonStyle.green, custom_id=f"add_{flower}", row=0))
            self.children[-1].callback = callback

    @discord.ui.button(label="Concocter", emoji="⚗️", style=discord.ButtonStyle.blurple)
    async def concocter(self, interaction, button):
        potion = POTIONS.get(str(self.value))
        supabase.table(TABLE_NAME).update({"inventory": self.temp_inventory}).eq("user_id", self.user_id).execute()
        if potion:
            await interaction.response.send_message(f"✨ Tu as créé : **{potion}** !", ephemeral=False)
        else:
            await interaction.response.send_message("💥 Ta mixture explose ! Rien obtenu...", ephemeral=False)
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
# 🎛️ UI — Boutons Jardin
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

        last = self.garden.get("last_fertilize")
        if last:
            try:
                last_dt = datetime.datetime.fromisoformat(last)
                now = datetime.datetime.now(datetime.timezone.utc)
                if now < last_dt + FERTILIZE_COOLDOWN:
                    remain = last_dt + FERTILIZE_COOLDOWN - now
                    total_seconds = int(remain.total_seconds())
                    minutes, seconds = divmod(total_seconds, 60)
                    hours, minutes = divmod(minutes, 60)
                    return await interaction.response.send_message(
                        f"⏳ Tu dois attendre {hours}h {minutes}m {seconds}s avant d'utiliser de l'engrais !",
                        ephemeral=True
                    )
            except Exception:
                pass

        self.garden["garden_grid"] = pousser_fleurs(self.garden["garden_grid"])
        self.garden["last_fertilize"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await self.update_garden_db()

        view = JardinView(self.garden, self.user_id)
        view.update_buttons()
        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Couper", emoji="✂️", style=discord.ButtonStyle.secondary)
    async def couper(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        new_lines, self.garden = couper_fleurs(self.garden["garden_grid"], self.garden)
        self.garden["garden_grid"] = new_lines
        await self.update_garden_db()

        view = JardinView(self.garden, self.user_id)
        view.update_buttons()
        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="Alchimie", emoji="⚗️", style=discord.ButtonStyle.blurple)
    async def alchimie(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)

        view = AlchimieView(self.garden, self.user_id)
        view.add_flower_buttons()
        embed = view.build_embed()
        await interaction.response.send_message(embed=embed, view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Jardin(commands.Cog):
    """Commande /jardin et !jardin — Voir son jardin"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_garden(self, target_user, viewer_id, respond_func):
        try:
            garden = await get_or_create_garden(target_user.id, target_user.name)
            embed = build_garden_embed(garden, viewer_id)
            view = None
            if target_user.id == viewer_id:
                view = JardinView(garden, viewer_id)
                view.update_buttons()
            await respond_func(embed=embed, view=view)
        except Exception as e:
            print(f"[ERREUR jardin] {e}")
            await respond_func("❌ Une erreur est survenue.", ephemeral=True)

    @app_commands.command(name="jardin", description="Affiche ton jardin ou celui d'un autre utilisateur 🌱")
    @app_commands.checks.cooldown(1, 5.0)
    async def slash_jardin(self, interaction:discord.Interaction, user:discord.User=None):
        target = user or interaction.user
        await self._send_garden(target, interaction.user.id, lambda **kwargs: safe_respond(interaction, **kwargs))

    @commands.command(name="jardin")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def prefix_jardin(self, ctx:commands.Context, user:discord.User=None):
        target = user or ctx.author
        await self._send_garden(target, ctx.author.id, lambda **kwargs: safe_send(ctx.channel, **kwargs))

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Jardin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeu"
    await bot.add_cog(cog)
