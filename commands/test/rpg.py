# ────────────────────────────────────────────────────────────────────────────────
# 📌 rpg_bleach.py — Mini RPG interactif /rpg_bleach et !rpg_bleach
# Objectif : Jeu interactif style "livre dont vous êtes le héros" dans l'univers Bleach
# Catégorie : Fun
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import json
import os
from utils.discord_utils import safe_send, safe_edit, safe_respond, safe_delete
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement du scénario RPG depuis JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "rpg_story.json")

def load_story():
    """Charge le scénario RPG depuis un fichier JSON."""
    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR RPG] Impossible de charger {DATA_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Connexion à Supabase pour les sauvegardes
# ────────────────────────────────────────────────────────────────────────────────
TABLE_NAME = "rpg"

def load_save(user_id: int):
    """Charge la sauvegarde d'un joueur depuis Supabase."""
    try:
        res = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).execute()
        if res.data:
            return res.data[0]
        else:
            return {"user_id": user_id, "username": None, "position": "intro", "inventory": []}
    except Exception as e:
        print(f"[ERREUR LOAD SAVE] {e}")
        return {"user_id": user_id, "username": None, "position": "intro", "inventory": []}

def save_player(data: dict):
    """Sauvegarde ou met à jour un joueur dans Supabase."""
    try:
        user_id = data["user_id"]
        existing = supabase.table(TABLE_NAME).select("*").eq("user_id", user_id).execute()
        if existing.data:
            supabase.table(TABLE_NAME).update(data).eq("user_id", user_id).execute()
        else:
            supabase.table(TABLE_NAME).insert(data).execute()
    except Exception as e:
        print(f"[ERREUR SAVE PLAYER] {e}")

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue et Boutons pour le RPG
# ────────────────────────────────────────────────────────────────────────────────
class RPGView(View):
    """Vue principale pour le RPG avec boutons de choix et inventaire."""
    def __init__(self, bot, save_data, data, user_id, current_key):
        super().__init__(timeout=120)
        self.bot = bot
        self.data = data
        self.saves = save_data
        self.user_id = str(user_id)
        self.current_key = current_key
        self.message = None
        # Création des boutons pour les choix
        options = data[current_key].get("options", {})
        for label, next_key in options.items():
            self.add_item(RPGButton(self, label, next_key))
        # Bouton pour inventaire
        self.add_item(InventoryButton(self))

    async def on_timeout(self):
        """Désactive les boutons quand la vue expire."""
        for child in self.children:
            child.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)

class RPGButton(Button):
    """Bouton pour choisir une option dans le RPG."""
    def __init__(self, parent_view: RPGView, label: str, next_key: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.parent_view = parent_view
        self.next_key = next_key

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.parent_view.user_id:
            await interaction.response.send_message(
                "❌ Ce n'est pas ton aventure !", ephemeral=True
            )
            return
        user_id = int(self.parent_view.user_id)
        self.parent_view.saves["position"] = self.next_key
        save_player({
            "user_id": user_id,
            "username": self.parent_view.saves.get("username", str(interaction.user)),
            "position": self.next_key,
            "inventory": self.parent_view.saves.get("inventory", [])
        })
        embed = build_rpg_embed(
            self.parent_view.data,
            self.next_key,
            self.parent_view.saves
        )
        new_view = RPGView(
            self.parent_view.bot,
            self.parent_view.saves,
            self.parent_view.data,
            user_id,
            self.next_key
        )
        new_view.message = interaction.message
        await safe_edit(interaction.message, embed=embed, view=new_view)

class InventoryButton(Button):
    """Bouton pour afficher l'inventaire du joueur."""
    def __init__(self, parent_view: RPGView):
        super().__init__(label="📦 Inventaire", style=discord.ButtonStyle.secondary)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.parent_view.user_id:
            await interaction.response.send_message(
                "❌ Tu ne peux pas voir l'inventaire de ce joueur.", ephemeral=True
            )
            return
        inventory = self.parent_view.saves.get("inventory", [])
        inv_text = "*(Inventaire vide)*" if not inventory else "\n".join(f"• {item}" for item in inventory)
        embed = discord.Embed(
            title="📦 Inventaire",
            description=inv_text,
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Génération de l'embed du RPG
# ────────────────────────────────────────────────────────────────────────────────
def build_rpg_embed(data, key, player_data):
    """Construit l'embed pour le paragraphe RPG courant."""
    description = data[key]["description"]
    embed = discord.Embed(
        title=f"📖 RPG Bleach — Étape : {key}",
        description=description,
        color=discord.Color.orange()
    )
    embed.add_field(name="Progression", value=key, inline=True)
    return embed

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class RPGBleach(commands.Cog):
    """Mini RPG interactif /rpg_bleach et !rpg_bleach"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🔹 Fonction interne pour démarrer le RPG
    async def _start_rpg(self, channel: discord.abc.Messageable, user: discord.User):
        data = load_story()
        if not data:
            await safe_send(channel, "❌ Impossible de charger le scénario RPG.")
            return
        # Charge la sauvegarde depuis Supabase
        save = load_save(user.id)
        if save["username"] is None:
            save["username"] = str(user)
        current_key = save["position"]
        embed = build_rpg_embed(data, current_key, save)
        view = RPGView(self.bot, save, data, user.id, current_key)
        view.message = await safe_send(channel, embed=embed, view=view)

    # 🔹 Commande SLASH
    @app_commands.command(
        name="rpg",
        description="Commence ou reprends ton RPG textuel dans l'univers de Bleach."
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.user.id))
    async def slash_rpg_bleach(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._start_rpg(interaction.channel, interaction.user)
            await interaction.delete_original_response()
        except app_commands.CommandOnCooldown as e:
            await safe_respond(interaction, f"⏳ Attends encore {e.retry_after:.1f}s.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /rpg_bleach] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # 🔹 Commande PREFIX
    @commands.command(name="rpg")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_rpg_bleach(self, ctx: commands.Context):
        try:
            await self._start_rpg(ctx.channel, ctx.author)
        except commands.CommandOnCooldown as e:
            await safe_send(ctx.channel, f"⏳ Attends encore {e.retry_after:.1f}s.")
        except Exception as e:
            print(f"[ERREUR !rpg_bleach] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = RPGBleach(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
