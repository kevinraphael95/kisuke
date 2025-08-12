# ──────────────────────────────────────────────────────────────
# 📁 REIATSU - GESTION DU SPAWN
# ──────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────
# 📦 IMPORTS
# ──────────────────────────────────────────────────────────────
import discord
import random
import time
import asyncio
from datetime import datetime
from dateutil import parser
from discord.ext import commands, tasks
from supabase_client import supabase
from utils.discord_utils import safe_send  # <-- Import fonctions sécurisées


# ──────────────────────────────────────────────────────────────
# 🎮 VIEW : Bouton pour absorber le Reiatsu (avec defer + followup)
# ──────────────────────────────────────────────────────────────
class AbsorberButtonView(discord.ui.View):
    def __init__(self, bot, guild_id, spawn_message_id):
        super().__init__(timeout=None)  # Pas de timeout automatique
        self.bot = bot
        self.guild_id = str(guild_id)
        self.spawn_message_id = str(spawn_message_id) if spawn_message_id is not None else None

    @discord.ui.button(label="Absorber", style=discord.ButtonStyle.blurple, emoji="💠")
    async def absorber_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Empêche le bot de cliquer sur son propre bouton
        if interaction.user.id == self.bot.user.id:
            return

        # ACK rapide pour éviter "Interaction failed"
        await interaction.response.defer(thinking=True)

        # Récupère config serveur (exécuté dans un thread pour éviter blocage)
        conf_data = await asyncio.to_thread(
            lambda: supabase.table("reiatsu_config").select("*").eq("guild_id", self.guild_id).execute()
        )
        if not conf_data.data:
            await interaction.followup.send("❌ Configuration du serveur introuvable.", ephemeral=True)
            return
        conf = conf_data.data[0]

        # Vérifie que le spawn est toujours valide
        if not conf.get("en_attente") or str(self.spawn_message_id) != str(conf.get("spawn_message_id")):
            # désactive le bouton si possible
            for item in self.children:
                item.disabled = True
            try:
                await interaction.message.edit(view=self)
            except Exception:
                pass
            await interaction.followup.send("❌ Ce Reiatsu n'est plus disponible.", ephemeral=True)
            return

        # Infos utiles
        guild = self.bot.get_guild(int(self.guild_id))
        user = interaction.user  # utiliser l'utilisateur de l'interaction
        channel = interaction.channel  # canal de l'interaction

        if not channel or not user:
            await interaction.followup.send("❌ Erreur interne : canal ou membre introuvable.", ephemeral=True)
            return

        # 🎲 Détermine si c'est un Super Reiatsu (1%)
        is_super = random.randint(1, 100) == 1
        gain = 100 if is_super else 1
        user_id = str(user.id)

        # Récupère classe, points et bonus5 (thread)
        user_data = await asyncio.to_thread(
            lambda: supabase.table("reiatsu").select("classe", "points", "bonus5").eq("user_id", user_id).execute()
        )
        if user_data.data:
            classe = user_data.data[0].get("classe")
            current_points = user_data.data[0]["points"]
            bonus5 = user_data.data[0].get("bonus5", 0) or 0
        else:
            classe = "Travailleur"
            current_points = 0
            bonus5 = 0

        # Gestion des passifs
        if not is_super:
            if classe == "Absorbeur":
                gain += 5
            elif classe == "Parieur":
                if random.random() < 0.5:
                    gain = 0
                else:
                    gain = random.randint(5, 12)
            if classe == "Travailleur":
                bonus5 += 1
                if bonus5 >= 5:
                    gain = 6
                    bonus5 = 0
        else:
            bonus5 = 0

        new_total = current_points + gain

        # Mise à jour ou insertion (thread)
        if user_data.data:
            await asyncio.to_thread(
                lambda: supabase.table("reiatsu").update({
                    "points": new_total,
                    "bonus5": bonus5
                }).eq("user_id", user_id).execute()
            )
        else:
            await asyncio.to_thread(
                lambda: supabase.table("reiatsu").insert({
                    "user_id": user_id,
                    "username": user.name,
                    "points": gain,
                    "classe": "Travailleur",
                    "bonus5": 1
                }).execute()
            )

        # Message de confirmation — utiliser followup (après defer)
        if is_super:
            await interaction.followup.send(f"🌟 {user.mention} a absorbé un **Super Reiatsu** et gagné **+{gain}** reiatsu !")
        else:
            if classe == "Parieur" and gain == 0:
                await interaction.followup.send(f"🎲 {user.mention} a tenté d’absorber un reiatsu mais a raté (passif Parieur) !")
            else:
                await interaction.followup.send(f"💠 {user.mention} a absorbé le Reiatsu et gagné **+{gain}** reiatsu !")

        # 🔄 Réinitialisation état (thread)
        new_delay = random.randint(1800, 5400)
        await asyncio.to_thread(
            lambda: supabase.table("reiatsu_config").update({
                "en_attente": False,
                "spawn_message_id": None,
                "delay_minutes": new_delay
            }).eq("guild_id", self.guild_id).execute()
        )

        # Désactivation du bouton visible
        for item in self.children:
            item.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            # si l'édition échoue, on ignore (mais on a déjà ack et envoyé la followup)
            pass


# ──────────────────────────────────────────────────────────────
# 🔧 COG : ReiatsuSpawner (spawn_loop envoie View)
# ──────────────────────────────────────────────────────────────
class ReiatsuSpawner(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.spawn_loop.start()  # 🔁 Lancement auto de la boucle

    def cog_unload(self):
        self.spawn_loop.cancel()  # 🛑 Arrêt boucle à l’unload

    # ──────────────────────────────────────────────────────────
    # ⏲️ TÂCHE : spawn_loop — toutes les 60 sec
    # ──────────────────────────────────────────────────────────
    @tasks.loop(seconds=60)
    async def spawn_loop(self):
        await self.bot.wait_until_ready()

        # 🔒 Instance principale uniquement
        if not getattr(self.bot, "is_main_instance", True):
            return

        now = int(time.time())

        # 📦 Récupère config serveurs
        configs = supabase.table("reiatsu_config").select("*").execute()

        for conf in configs.data:
            guild_id = conf["guild_id"]
            channel_id = conf.get("channel_id")
            en_attente = conf.get("en_attente", False)
            delay = conf.get("delay_minutes") or 1800

            if not channel_id or en_attente:
                continue

            last_spawn_str = conf.get("last_spawn_at")
            should_spawn = not last_spawn_str or (
                now - int(parser.parse(last_spawn_str).timestamp()) >= delay
            )
            if not should_spawn:
                continue

            channel = self.bot.get_channel(int(channel_id))
            if not channel:
                continue

            # ✨ Envoie du spawn avec bouton
            embed = discord.Embed(
                title="💠 Un Reiatsu sauvage apparaît !",
                description="Cliquez sur le bouton ci-dessous pour l'absorber.",
                color=discord.Color.purple()
            )

            view = AbsorberButtonView(self.bot, guild_id, None)

            # safe_send peut ne pas accepter 'view' selon ton wrapper — fallback géré
            try:
                message = await safe_send(channel, embed=embed, view=view)
            except TypeError:
                # si safe_send n'accepte pas view, utiliser channel.send directement
                message = await channel.send(embed=embed, view=view)

            # Ajoute l'ID du message à la View
            view.spawn_message_id = message.id

            # 💾 Mise à jour état (non bloquant rapide)
            supabase.table("reiatsu_config").update({
                "en_attente": True,
                "last_spawn_at": datetime.utcnow().isoformat(),
                "spawn_message_id": str(message.id)
            }).eq("guild_id", guild_id).execute()


# ──────────────────────────────────────────────────────────────
# 🔌 SETUP AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ReiatsuSpawner(bot))

    # Restaure les Views des Reiatsu en attente après reboot
    configs = supabase.table("reiatsu_config").select("*").execute()
    for conf in configs.data:
        if conf.get("en_attente") and conf.get("spawn_message_id") and conf.get("guild_id"):
            guild_id = conf["guild_id"]
            spawn_message_id = conf["spawn_message_id"]
            view = AbsorberButtonView(bot, guild_id, spawn_message_id)
            bot.add_view(view)  # Important : relie la View au message Discord existant







