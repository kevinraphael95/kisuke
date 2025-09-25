# ──────────────────────────────────────────────────────────────
# 📌 debugreiatsu.py — Commande admin /debugreiatsu et !debugreiatsu
# Objectif : Vérifier l'état du spawner Reiatsu et déclencher un spawn manuel
# Catégorie : Admin
# Accès : Administrateurs uniquement
# ──────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import time, random, json, os
from dateutil import parser
from utils.discord_utils import safe_send
from utils.supabase_client import supabase

DATA_JSON_PATH = os.path.join("data", "reiatsu_config.json")



def load_data():
    """Charge la configuration Reiatsu depuis le fichier JSON."""
    try:
        with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERREUR JSON] Impossible de charger {DATA_JSON_PATH} : {e}")
        return {}

def format_seconds(sec: int) -> str:
    """Formate un temps en secondes -> Xh Ym Zs"""
    if sec is None:
        return "N/A"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    if h: return f"{h}h {m}m {s}s"
    if m: return f"{m}m {s}s"
    return f"{s}s"

class DebugReiatsu(commands.Cog):
    """Commande /debugreiatsu et !debugreiatsu"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = load_data()
        self.SPAWN_SPEED_RANGES = self.config.get("SPAWN_SPEED_RANGES", {})
        self.DEFAULT_SPAWN_SPEED = self.config.get("DEFAULT_SPAWN_SPEED", "Normal")
        self.SPAWN_LOOP_INTERVAL = self.config.get("SPAWN_LOOP_INTERVAL", 60)

    # ──────────────────────────────────────────────────────────
    async def _send_debug(self, channel: discord.abc.Messageable, guild: discord.Guild, force: bool = False, reset: bool = False):
        try:
            conf_data = supabase.table("reiatsu_config").select("*").eq("guild_id", str(guild.id)).execute().data
            if not conf_data:
                await safe_send(channel, "⚠️ Aucune configuration trouvée pour ce serveur.")
                return

            conf = conf_data[0]
            now = int(time.time())

            # Spawn timing
            spawn_speed = conf.get("spawn_speed") or self.DEFAULT_SPAWN_SPEED
            min_delay, max_delay = self.SPAWN_SPEED_RANGES.get(
                spawn_speed, self.SPAWN_SPEED_RANGES.get(self.DEFAULT_SPAWN_SPEED, (30, 60))
            )
            delay = conf.get("spawn_delay") or random.randint(min_delay, max_delay)
            last_spawn_str = conf.get("last_spawn_at")
            last_spawn_ts = int(parser.parse(last_spawn_str).timestamp()) if last_spawn_str else None
            remaining = (last_spawn_ts + delay - now) if last_spawn_ts else None

            # Couleur dynamique
            if not conf.get("is_spawn"):
                color = discord.Color.red()
            elif remaining and remaining > 0:
                color = discord.Color.orange()
            else:
                color = discord.Color.green()

            embed = discord.Embed(
                title="🔧 Debug Reiatsu",
                description=f"📊 État du spawner pour **{guild.name}**",
                color=color
            )

            # Infos serveur
            embed.add_field(name="🆔 Guild ID", value=guild.id, inline=True)
            embed.add_field(name="👥 Membres", value=guild.member_count, inline=True)
            embed.add_field(name="💬 Salons", value=len(guild.channels), inline=True)

            # Infos bot / loop
            embed.add_field(name="📦 Main Instance", value="✅ Oui" if getattr(self.bot, "is_main_instance", True) else "❌ Non", inline=True)
            embed.add_field(name="🔁 Loop interval", value=f"{self.SPAWN_LOOP_INTERVAL}s", inline=True)
            loop_status = "✅ Running" if getattr(self.bot, "reiatsu_loop_running", True) else "❌ Stopped"
            embed.add_field(name="⚙️ Loop status", value=loop_status, inline=True)

            # Infos spawn timing
            embed.add_field(name="⚡ Vitesse", value=f"{spawn_speed} ({min_delay}-{max_delay}s)", inline=True)
            embed.add_field(name="⏳ Délai actuel", value=f"{delay}s", inline=True)
            embed.add_field(name="⏰ Dernier spawn", value=f"<t:{last_spawn_ts}:R>" if last_spawn_ts else "Jamais", inline=True)
            embed.add_field(name="⌛ Temps restant", value=f"{format_seconds(remaining)} ({remaining}s)" if remaining else "N/A", inline=True)

            # Config active
            embed.add_field(name="💬 Salon configuré", value=f"<#{conf.get('channel_id')}>" if conf.get("channel_id") else "Aucun", inline=True)
            embed.add_field(
                name="📩 Message ID",
                value=f"[{conf.get('message_id')}](https://discord.com/channels/{guild.id}/{conf.get('channel_id')}/{conf.get('message_id')})"
                if conf.get("message_id") else "None",
                inline=True
            )
            embed.add_field(name="🚦 Spawn actif", value="✅ Oui" if conf.get("is_spawn") else "❌ Non", inline=True)

            # Infos DB globale
            try:
                players_count = supabase.table("reiatsu").select("user_id", count="exact").execute().count
            except Exception:
                players_count = "?"
            embed.add_field(name="📊 Joueurs inscrits", value=players_count, inline=True)

            # Actions
            if force:
                try:
                    reiatsu_cog = self.bot.get_cog("ReiatsuSpawner")
                    if reiatsu_cog:
                        channel_obj = self.bot.get_channel(int(conf.get("channel_id", 0)))
                        if channel_obj:
                            await reiatsu_cog._spawn_message(channel_obj, guild.id)
                            embed.add_field(name="🔥 Action forcée", value="✅ Spawn déclenché manuellement", inline=False)
                        else:
                            embed.add_field(name="🔥 Action forcée", value="❌ Salon introuvable", inline=False)
                    else:
                        embed.add_field(name="🔥 Action forcée", value="❌ ReiatsuSpawner introuvable", inline=False)
                except Exception as e:
                    embed.add_field(name="🔥 Action forcée", value=f"❌ Erreur : {e}", inline=False)

            if reset:
                try:
                    supabase.table("reiatsu_config").update({
                        "is_spawn": False,
                        "message_id": None,
                        "last_spawn_at": None,
                        "spawn_delay": None
                    }).eq("guild_id", str(guild.id)).execute()
                    embed.add_field(name="♻️ Reset config", value="✅ Config remise à zéro", inline=False)
                except Exception as e:
                    embed.add_field(name="♻️ Reset config", value=f"❌ Erreur : {e}", inline=False)

            await safe_send(channel, embed=embed)

        except Exception as e:
            await safe_send(channel, f"❌ Une erreur est survenue : {e}")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="debugreiatsu")
    @commands.has_permissions(administrator=True)
    async def prefix_debugreiatsu(self, ctx: commands.Context, arg: str = None):
        force = arg == "force"
        reset = arg == "reset"
        await self._send_debug(ctx.channel, ctx.guild, force=force, reset=reset)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────    
    @app_commands.command(
        name="debugreiatsu",
        description="Affiche l'état du spawner Reiatsu (options: force / reset)"
    )
    async def slash_debugreiatsu(self, interaction: discord.Interaction, force: bool = False, reset: bool = False):
        await interaction.response.defer(ephemeral=True)
        await self._send_debug(interaction.channel, interaction.guild, force=force, reset=reset)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = DebugReiatsu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
