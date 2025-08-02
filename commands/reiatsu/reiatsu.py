# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu.py — Commande interactive !reiatsu
# Objectif : Affiche le score Reiatsu d’un membre, le salon de spawn et le temps restant
# Catégorie : Reiatsu
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from dateutil import parser
from datetime import datetime, timedelta
import time
from supabase_client import supabase
import json

from utils.discord_utils import safe_send, safe_respond  # <-- import fonctions anti 429

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Reiatsu2Command(commands.Cog):
    """
    Commande !reiatsu — Affiche ton score de Reiatsu, le salon et le temps avant le prochain spawn.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="reiatsu",
        aliases=["rts"],
        help="💠 Affiche le score de Reiatsu d’un membre (ou soi-même).",
        description="Affiche le score, le salon de spawn et le temps restant avant le prochain Reiatsu."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def reiatsu(self, ctx: commands.Context, member: discord.Member = None):
        user = member or ctx.author
        user_id = str(user.id)
        guild_id = str(ctx.guild.id) if ctx.guild else None

        # 📦 Requête : Données joueur
        user_data = supabase.table("reiatsu") \
            .select("points, classe, last_steal_attempt, steal_cd") \
            .eq("user_id", user_id) \
            .execute()
        data = user_data.data[0] if user_data.data else {}

        points = data.get("points", 0)
        classe_nom = data.get("classe")
        last_steal_str = data.get("last_steal_attempt")
        steal_cd = data.get("steal_cd")

        # 🔁 Chargement des infos de la classe (si elle existe)
        with open("data/classes.json", "r", encoding="utf-8") as f:
            CLASSES = json.load(f)

        if classe_nom and classe_nom in CLASSES:
            classe_text = (
                f"• Classe : **{classe_nom}**\n"
                f"• Compétence passive : {CLASSES[classe_nom]['Passive']}\n"
                f"• Compétence active : {CLASSES[classe_nom]['Active']}\n"
                f"(les compétences actives ne sont pas ajoutées)"
            )
        else:
            classe_text = "Aucune classe sélectionnée.\nUtilise la commande `!classe` pour en choisir une."

        # 📦 Gestion du cooldown dynamique
        cooldown_text = "Disponible ✅"
        if classe_nom and steal_cd is None:
            steal_cd = 19 if classe_nom == "Voleur" else 24
            supabase.table("reiatsu").update({"steal_cd": steal_cd}).eq("user_id", user_id).execute()

        if last_steal_str and steal_cd:
            last_steal = parser.parse(last_steal_str)
            next_steal = last_steal + timedelta(hours=steal_cd)
            now = datetime.utcnow()
            if now < next_steal:
                restant = next_steal - now
                minutes_total = int(restant.total_seconds() // 60)
                h, m = divmod(minutes_total, 60)
                cooldown_text = f"{restant.days}j {h}h{m}m" if restant.days else f"{h}h{m}m"

        # 📦 Requête : Configuration serveur
        config = None
        salon_text = "❌"
        temps_text = "❌"

        if ctx.guild:
            config_data = supabase.table("reiatsu_config") \
                .select("*") \
                .eq("guild_id", guild_id) \
                .execute()
            config = config_data.data[0] if config_data.data else None

            # 🛠️ Préparation des infos config
            salon_text = "❌ Aucun salon configuré"
            temps_text = "⚠️ Inconnu"
            if config:
                salon = ctx.guild.get_channel(int(config["channel_id"])) if config.get("channel_id") else None
                salon_text = salon.mention if salon else "⚠️ Salon introuvable"
                if config.get("en_attente"):
                    channel_id = config.get("channel_id")
                    msg_id = config.get("spawn_message_id")
                    if msg_id and channel_id:
                        link = f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}"
                        temps_text = f"Un Reiatsu 💠 est **déjà apparu** ! [Aller le prendre]({link})"
                    else:
                        temps_text = "Un Reiatsu 💠 est **déjà apparu** ! (Lien indisponible)"
                else:
                    last_spawn = config.get("last_spawn_at")
                    delay = config.get("delay_minutes", 1800)
                    if last_spawn:
                        last_ts = parser.parse(last_spawn).timestamp()
                        now_ts = time.time()
                        remaining = int((last_ts + delay) - now_ts)
                        if remaining <= 0:
                            temps_text = "💠 Un Reiatsu peut apparaître **à tout moment** !"
                        else:
                            minutes, seconds = divmod(remaining, 60)
                            temps_text = f"**{minutes}m {seconds}s**"
                    else:
                        temps_text = "Un Reiatsu 💠 peut apparaître **à tout moment** !"

        # 📋 Création de l'embed
        embed = discord.Embed(
            title="__**💠 Profil**__",
            description=(
                f"**{user.display_name}** a actuellement :\n"
                f"**{points}** points de Reiatsu\n"
                f"• 🕵️ Cooldown vol : {cooldown_text} (!!reiatsuvol pour voler du reiatsu à quelqu'un)\n\n"
                f"__**Classe**__\n"
                f"{classe_text}\n\n"
                f"__**Spawn du reiatsu**__\n"
                f"• 📍 Lieu d'apparition : {salon_text}\n"
                f"• ⏳ Temps avant apparition : {temps_text}"
            ),
            color=discord.Color.purple()
        )
        embed.set_footer(text="Réagis avec 📊 pour voir le classement.")

        msg = await safe_send(ctx.channel, embed=embed)
        await msg.add_reaction("📊")

        # 🔁 Écoute de la réaction
        def check(reaction, user_check):
            return (
                reaction.message.id == msg.id and
                str(reaction.emoji) == "📊" and
                user_check == ctx.author
            )

        try:
            await self.bot.wait_for("reaction_add", check=check, timeout=30)
            await self.show_leaderboard(ctx, original_message=msg)
        except Exception:
            pass  # Timeout ou autre erreur : on ignore

    async def show_leaderboard(self, ctx: commands.Context, original_message=None):
        # 📦 Requête : Top 10 joueurs avec uniquement username
        leaderboard_resp = supabase.table("reiatsu") \
            .select("username, points") \
            .order("points", desc=True) \
            .limit(10) \
            .execute()

        leaderboard = leaderboard_resp.data if leaderboard_resp.data else []

        # 📄 Formatage du classement
        top_texte = ""
        for i, entry in enumerate(leaderboard, start=1):
            name = entry.get("username", "Inconnu")
            points = entry["points"]
            top_texte += f"**#{i}** — {name} : {points} pts\n"

        # 🖼️ Embed du classement
        embed = discord.Embed(
            title="📊 Top 10 des utilisateurs avec le plus de Reiatsu",
            description=top_texte,
            color=discord.Color.gold()
        )
        await safe_send(ctx.channel, embed=embed, reference=original_message)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Reiatsu2Command(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
