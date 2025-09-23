# ────────────────────────────────────────────────────────────────────────────────
# 📌 debugreiatsu.py — Commande admin /debugreiatsu et !debugreiatsu
# Objectif : Vérifier l'état du spawner Reiatsu et déclencher un spawn manuel
# Catégorie : Admin
# Accès : Administrateurs uniquement
# Cooldown : 1 utilisation / 5 sec par utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import time
import random
import json
import os
from dateutil import parser
from utils.discord_utils import safe_send
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON (reiatsu_config.json)
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "reiatsu_config.json")

def load_data():
    """Charge la configuration Reiatsu depuis le fichier JSON."""
    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {DATA_JSON_PATH} : {e}")
        return {}

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class DebugReiatsu(commands.Cog):
    """
    Commande /debugreiatsu et !debugreiatsu — Vérifie l'état du spawner et force un spawn
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_data()
        self.SPAWN_SPEED_RANGES = self.config.get("SPAWN_SPEED_RANGES", {})
        self.DEFAULT_SPAWN_SPEED = self.config.get("DEFAULT_SPAWN_SPEED", "Normal")
        self.SPAWN_LOOP_INTERVAL = self.config.get("SPAWN_LOOP_INTERVAL", 60)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonction interne commune
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_debug(self, channel: discord.abc.Messageable, guild: discord.Guild, force: bool = False):
        conf = supabase.table("reiatsu_config").select("*").eq("guild_id", str(guild.id)).execute()
        if not conf.data:
            await safe_send(channel, "⚠️ Aucune configuration trouvée pour ce serveur.")
            return

        conf = conf.data[0]
        last_spawn_str = conf.get("last_spawn_at")
        spawn_speed = conf.get("spawn_speed") or self.DEFAULT_SPAWN_SPEED
        min_delay, max_delay = self.SPAWN_SPEED_RANGES.get(spawn_speed, self.SPAWN_SPEED_RANGES[self.DEFAULT_SPAWN_SPEED])
        delay = conf.get("spawn_delay") or random.randint(min_delay, max_delay)
        now = int(time.time())
        last_spawn_ts = int(parser.parse(last_spawn_str).timestamp()) if last_spawn_str else None
        remaining = (last_spawn_ts + delay - now) if last_spawn_ts else None

        embed = discord.Embed(
            title="🔧 Debug Reiatsu",
            description=f"État du spawner pour **{guild.name}**",
            color=discord.Color.purple()
        )
        embed.add_field(name="Instance principale", value="✅ Oui" if getattr(self.bot, "is_main_instance", True) else "❌ Non", inline=True)
        embed.add_field(name="Task Loop", value=f"Toutes les `{self.SPAWN_LOOP_INTERVAL}` sec", inline=True)
        embed.add_field(name="Spawn en cours", value="✅ Oui" if conf.get("is_spawn") else "❌ Non", inline=True)
        embed.add_field(name="Dernier spawn", value=last_spawn_str or "Jamais", inline=False)
        embed.add_field(name="Délai défini", value=f"{delay} sec (range {min_delay}-{max_delay})", inline=True)
        embed.add_field(name="Temps restant", value=f"{remaining} sec" if remaining is not None else "N/A", inline=True)
        embed.add_field(name="Salon configuré", value=f"<#{conf.get('channel_id')}>" if conf.get("channel_id") else "Aucun", inline=False)
        embed.add_field(name="Message ID", value=conf.get("message_id") or "None", inline=True)

        if force:
            # 🔥 Déclenchement du spawn manuel
            try:
                reiatsu_cog = self.bot.get_cog("ReiatsuSpawner")
                if reiatsu_cog:
                    channel_obj = self.bot.get_channel(conf.get("channel_id"))
                    if channel_obj:
                        await reiatsu_cog._spawn_message(channel_obj, guild.id)
                        embed.add_field(name="Action forcée", value="✅ Spawn déclenché manuellement", inline=False)
                        print(f"[DEBUG] Spawn forcé déclenché pour {guild.id}")
                    else:
                        embed.add_field(name="Action forcée", value="❌ Salon introuvable", inline=False)
                else:
                    embed.add_field(name="Action forcée", value="❌ ReiatsuSpawner introuvable", inline=False)
            except Exception as e:
                embed.add_field(name="Action forcée", value=f"❌ Erreur lors du spawn : {e}", inline=False)

        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="debugreiatsu",
        description="Affiche l'état du spawner Reiatsu (option: force un spawn)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_debugreiatsu(self, interaction: discord.Interaction, force: bool = False):
        await interaction.response.defer(ephemeral=True)
        await self._send_debug(interaction.channel, interaction.guild, force=force)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="debugreiatsu")
    @commands.has_permissions(administrator=True)
    async def prefix_debugreiatsu(self, ctx: commands.Context, arg: str = None):
        force = arg == "force"
        await self._send_debug(ctx.channel, ctx.guild, force=force)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = DebugReiatsu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
