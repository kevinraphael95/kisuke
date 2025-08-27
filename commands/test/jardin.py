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
import json
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
DEFAULT_GRID = ["🌱"*8]*3
DEFAULT_INVENTORY = {f:0 for f in ["tulipes","roses","jacinthes","hibiscus","paquerettes","tournesols"]}

FLEUR_EMOJIS = {"tulipes":"🌷","roses":"🌹","jacinthes":"🪻","hibiscus":"🌺","paquerettes":"🌼","tournesols":"🌻"}
FLEUR_LIST = list(FLEUR_EMOJIS.items())

FLEUR_VALUES = {"tulipes":1,"roses":2,"jacinthes":2,"hibiscus":3,"paquerettes":1,"tournesols":2}
FLEUR_SIGNS  = {"tulipes":"+","roses":"+","jacinthes":"×","hibiscus":"×","paquerettes":"-","tournesols":"-"}

with open("data/potions.json", "r", encoding="utf-8") as f:
    POTIONS = json.load(f)

FERTILIZE_COOLDOWN = datetime.timedelta(minutes=10)
FERTILIZE_PROBABILITY = 0.39
VIEW_TIMEOUT = 180  # 3 minutes

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonctions utilitaires
# ────────────────────────────────────────────────────────────────────────────────
async def get_or_create_garden(user_id:int, username:str):
    res = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).execute()
    if res.data:
        return res.data[0]
    new_garden = {"user_id":user_id,"username":username,"garden_grid":DEFAULT_GRID.copy(),
                  "inventory":DEFAULT_INVENTORY.copy(),"argent":0,"armee":"","last_fertilize":None}
    supabase.table(TABLE_NAME).insert(new_garden).execute()
    return new_garden

def build_garden_embed(garden:dict, viewer_id:int) -> discord.Embed:
    lines = garden["garden_grid"]
    inv = " / ".join(f"{FLEUR_EMOJIS[f]}{garden['inventory'].get(f,0)}" for f in FLEUR_EMOJIS)
    cd_str = "✅ Disponible"
    if garden.get("last_fertilize"):
        try:
            last_dt = datetime.datetime.fromisoformat(garden["last_fertilize"])
            now = datetime.datetime.now(datetime.timezone.utc)
            remain = last_dt + FERTILIZE_COOLDOWN - now
            if remain.total_seconds() > 0:
                total_seconds = int(remain.total_seconds())
                minutes, seconds = divmod(total_seconds, 60)
                hours, minutes = divmod(minutes, 60)
                cd_str = f"⏳ {hours}h {minutes}m {seconds}s"
        except Exception as e:
            print(f"[ERREUR parse last_fertilize] {e}")
    embed = discord.Embed(title=f"🏡 Jardin de {garden['username']}",
                          description="\n".join(lines), color=discord.Color.green())
    embed.add_field(name="Infos",
                    value=f"Fleurs possédées : {inv}\nArmée : {garden['armee'] or '—'} | Argent : {garden['argent']}💰\nCooldown engrais : {cd_str}",
                    inline=False)
    return embed

def pousser_fleurs(lines:list[str]) -> list[str]:
    new_lines = []
    for line in lines:
        chars = []
        for c in line:
            if c=="🌱" and random.random() < FERTILIZE_PROBABILITY:
                _, emoji = random.choice(FLEUR_LIST)
                chars.append(emoji)
            else: chars.append(c)
        new_lines.append("".join(chars))
    return new_lines

def couper_fleurs(lines:list[str], garden:dict) -> tuple[list[str],dict]:
    new_lines = []
    inv = garden["inventory"]
    for line in lines:
        chars = []
        for c in line:
            for f, emoji in FLEUR_EMOJIS.items():
                if c==emoji:
                    inv[f] = inv.get(f,0)+1
                    c="🌱"
            chars.append(c)
        new_lines.append("".join(chars))
    garden["inventory"] = inv
    return new_lines, garden

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Alchimie interactive
# ────────────────────────────────────────────────────────────────────────────────
class AlchimieView(discord.ui.View):
    def __init__(self, garden:dict, user_id:int, timeout=VIEW_TIMEOUT):
        super().__init__(timeout=timeout)
        self.garden = garden
        self.user_id = user_id
        self.original_inventory = garden["inventory"].copy()
        self.temp_inventory = garden["inventory"].copy()
        self.value = 0
        self.selected_flowers = []
        self.message: discord.Message = None

    def build_embed(self):
        fleurs_grouped = {"+":[],"×":[],"-":[]}
        for f in FLEUR_EMOJIS:
            fleurs_grouped[FLEUR_SIGNS[f]].append(f"{FLEUR_EMOJIS[f]}{FLEUR_SIGNS[f]}{FLEUR_VALUES[f]}")
        fleurs = "  ".join(" ".join(fleurs_grouped[s]) for s in ("+","×","-"))
        chosen = " ".join(FLEUR_EMOJIS[f] for f in self.selected_flowers) if self.selected_flowers else "—"
        return discord.Embed(title="⚗️ Alchimie",
                             description=f"Valeurs de fleurs : {fleurs}\n\n⚗️ {chosen}\nValeur : **{self.value}**",
                             color=discord.Color.purple())

    async def update_message(self, interaction:discord.Interaction):
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    def use_flower(self, flower:str) -> bool:
        if self.temp_inventory.get(flower,0)<=0: return False
        self.temp_inventory[flower]-=1
        self.selected_flowers.append(flower)
        sign = FLEUR_SIGNS[flower]
        val = FLEUR_VALUES[flower]
        if sign=="+": self.value+=val
        elif sign=="-": self.value-=val
        elif sign=="×": self.value = self.value*val if self.value!=0 else val
        return True

    # ───────── Boutons fleurs ─────────
    @discord.ui.button(label="🌷", style=discord.ButtonStyle.green)
    async def add_tulipe(self, interaction, button): await self._use_flower(interaction,"tulipes","🌷")
    @discord.ui.button(label="🌹", style=discord.ButtonStyle.green)
    async def add_rose(self, interaction, button): await self._use_flower(interaction,"roses","🌹")
    @discord.ui.button(label="🪻", style=discord.ButtonStyle.green)
    async def add_jacinthe(self, interaction, button): await self._use_flower(interaction,"jacinthes","🪻")
    @discord.ui.button(label="🌺", style=discord.ButtonStyle.green)
    async def add_hibiscus(self, interaction, button): await self._use_flower(interaction,"hibiscus","🌺")
    @discord.ui.button(label="🌼", style=discord.ButtonStyle.green)
    async def add_paquerette(self, interaction, button): await self._use_flower(interaction,"paquerettes","🌼")
    @discord.ui.button(label="🌻", style=discord.ButtonStyle.green)
    async def add_tournesol(self, interaction, button): await self._use_flower(interaction,"tournesols","🌻")

    async def _use_flower(self, interaction, flower, emoji):
        if not self.use_flower(flower):
            return await interaction.response.send_message(f"❌ Tu n’as plus de {emoji} !", ephemeral=True)
        await self.update_message(interaction)

    # ───────── Concocter & Reset ─────────
    @discord.ui.button(label="Concocter", emoji="⚗️", style=discord.ButtonStyle.blurple)
    async def concocter(self, interaction, button):
        potion = POTIONS.get(str(self.value))
        supabase.table(TABLE_NAME).update({"inventory": self.temp_inventory}).eq("user_id",self.user_id).execute()
        if potion: await interaction.response.send_message(f"✨ Tu as créé : **{potion}** !", ephemeral=False)
        else: await interaction.response.send_message("💥 Ta mixture explose ! Rien obtenu...", ephemeral=False)
        self.stop()

    @discord.ui.button(label="Reset", emoji="🔄", style=discord.ButtonStyle.red)
    async def reset(self, interaction, button):
        self.temp_inventory = self.original_inventory.copy()
        self.value=0
        self.selected_flowers=[]
        await self.update_message(interaction)

    async def interaction_check(self, interaction):
        return interaction.user.id==self.user_id

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Button): child.disabled=True
        if self.message:
            try: await self.message.edit(view=self)
            except: pass

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Jardin interactive
# ────────────────────────────────────────────────────────────────────────────────
class JardinView(discord.ui.View):
    def __init__(self, garden:dict, user_id:int, timeout=VIEW_TIMEOUT):
        super().__init__(timeout=timeout)
        self.garden = garden
        self.user_id = user_id
        self.message: discord.Message = None

    def update_buttons(self):
        last = self.garden.get("last_fertilize")
        disabled = False
        if last:
            try:
                last_dt = datetime.datetime.fromisoformat(last)
                now = datetime.datetime.now(datetime.timezone.utc)
                disabled = now < last_dt+FERTILIZE_COOLDOWN
            except: pass
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.label=="Engrais":
                child.disabled=disabled

    async def update_garden_db(self):
        supabase.table(TABLE_NAME).update({
            "garden_grid":self.garden["garden_grid"],
            "inventory":self.garden["inventory"],
            "last_fertilize":self.garden["last_fertilize"],
            "argent":self.garden["argent"],
            "armee":self.garden["armee"]
        }).eq("user_id",self.user_id).execute()

    @discord.ui.button(label="Engrais", emoji="💩", style=discord.ButtonStyle.green)
    async def engrais(self, interaction, button):
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
                    minutes, seconds = divmod(total_seconds,60)
                    hours, minutes = divmod(minutes,60)
                    return await interaction.response.send_message(f"⏳ Tu dois attendre {hours}h {minutes}m {seconds}s avant d'utiliser de l'engrais !", ephemeral=True)
            except: pass
        self.garden["garden_grid"] = pousser_fleurs(self.garden["garden_grid"])
        self.garden["last_fertilize"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        await self.update_garden_db()
        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Couper", emoji="✂️", style=discord.ButtonStyle.secondary)
    async def couper(self, interaction, button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)
        new_lines, self.garden = couper_fleurs(self.garden["garden_grid"], self.garden)
        self.garden["garden_grid"]=new_lines
        await self.update_garden_db()
        embed = build_garden_embed(self.garden, self.user_id)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Alchimie", emoji="⚗️", style=discord.ButtonStyle.blurple)
    async def alchimie(self, interaction, button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Ce jardin n'est pas à toi !", ephemeral=True)
        view = AlchimieView(self.garden,self.user_id)
        embed = view.build_embed()
        msg = await interaction.response.send_message(embed=embed, view=view)
        view.message = msg

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child,discord.ui.Button): child.disabled=True
        if self.message:
            try: await self.message.edit(view=self)
            except: pass

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Jardin(commands.Cog):
    """Commande /jardin et !jardin — Voir son jardin"""

    def __init__(self, bot:commands.Bot): self.bot=bot

    async def _send_garden(self, target_user, viewer_id, respond_func):
        try:
            garden = await get_or_create_garden(target_user.id, target_user.name)
            embed = build_garden_embed(garden, viewer_id)
            view = None
            if target_user.id==viewer_id:
                view = JardinView(garden, viewer_id)
                view.update_buttons()
            await respond_func(embed=embed, view=view)
        except Exception as e:
            print(f"[ERREUR jardin] {e}")
            await respond_func("❌ Une erreur est survenue.", ephemeral=True)

    # ───────── Commande Slash ─────────
    @app_commands.command(name="jardin", description="Affiche ton jardin ou celui d'un autre utilisateur 🌱")
    @app_commands.checks.cooldown(1, 5.0)  # 1 utilisation toutes les 5 secondes par utilisateur
    async def slash_jardin(self, interaction:discord.Interaction, user:discord.User=None):
        target = user or interaction.user
        await self._send_garden(target, interaction.user.id, lambda **kwargs: safe_respond(interaction, **kwargs))

    # ───────── Commande avec Préfixe ─────────
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
            command.category = "Test"
    await bot.add_cog(cog)
