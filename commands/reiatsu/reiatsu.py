# ────────────────────────────────────────────────────────────────────────────────
# 📌 reiatsu.py — Commande interactive /reiatsu et !reiatsu
# Objectif : Affiche le profil complet Reiatsu et propose toutes les actions
# Catégorie : Reiatsu
# Accès : Public
# Cooldown : 1 utilisation / 3 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Select
from dateutil import parser
from datetime import datetime, timedelta
import time
import json
import random

from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Vue principale du profil Reiatsu
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuView(View):
    def __init__(self, author: discord.Member, guild: discord.Guild, spawn_link: str = None):
        super().__init__(timeout=None)
        self.author = author
        self.guild = guild

        if spawn_link:
            self.add_item(Button(label="💠 Aller au spawn", style=discord.ButtonStyle.link, url=spawn_link))

        self.add_item(Button(label="📊 Classement", style=discord.ButtonStyle.primary, custom_id="reiatsu:classement"))
        self.add_item(Button(label="⚡ Éveil", style=discord.ButtonStyle.success, custom_id="reiatsu:eveil"))
        self.add_item(Button(label="🎭 Changer de classe", style=discord.ButtonStyle.secondary, custom_id="reiatsu:classe"))
        self.add_item(Button(label="🕵️ Voler du Reiatsu", style=discord.ButtonStyle.danger, custom_id="reiatsu:vol"))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ReiatsuCommand(commands.Cog):
    """Commande /reiatsu et !reiatsu — Affiche le profil complet et actions disponibles"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Profil Reiatsu
    # ────────────────────────────────────────────────────────────────────────────
    async def _send_profile(self, ctx_or_interaction, author, guild, target_user):
        user = target_user or author
        user_id = str(user.id)
        guild_id = str(guild.id) if guild else None

        user_data = supabase.table("reiatsu").select("points, classe, last_steal_attempt, steal_cd").eq("user_id", user_id).execute()
        data = user_data.data[0] if user_data.data else {}
        points = data.get("points", 0)
        classe_nom = data.get("classe")
        last_steal_str = data.get("last_steal_attempt")
        steal_cd = data.get("steal_cd")

        with open("data/classes.json", "r", encoding="utf-8") as f:
            CLASSES = json.load(f)
        if classe_nom and classe_nom in CLASSES:
            classe_text = f"• Classe : {classe_nom}\n• Passive : {CLASSES[classe_nom]['Passive']}\n• Active : {CLASSES[classe_nom]['Active']}"
        else:
            classe_text = "Aucune classe sélectionnée."

        # Cooldown vol
        cooldown_text = "Disponible ✅"
        if last_steal_str and steal_cd:
            last_steal = parser.parse(last_steal_str)
            next_steal = last_steal + timedelta(hours=steal_cd)
            now = datetime.utcnow()
            if now < next_steal:
                restant = next_steal - now
                minutes_total = int(restant.total_seconds() // 60)
                h, m = divmod(minutes_total, 60)
                cooldown_text = f"{restant.days}j {h}h{m}m" if restant.days else f"{h}h{m}m"

        # Spawn Reiatsu
        salon_text, temps_text, spawn_link = "❌", "❌", None
        if guild:
            config_data = supabase.table("reiatsu_config").select("*").eq("guild_id", guild_id).execute()
            config = config_data.data[0] if config_data.data else None
            if config:
                salon = guild.get_channel(int(config["channel_id"])) if config.get("channel_id") else None
                salon_text = salon.mention if salon else "⚠️ Salon introuvable"
                if config.get("en_attente"):
                    channel_id = config.get("channel_id")
                    msg_id = config.get("spawn_message_id")
                    if msg_id and channel_id:
                        spawn_link = f"https://discord.com/channels/{guild_id}/{channel_id}/{msg_id}"
                        temps_text = f"Un Reiatsu 💠 est déjà apparu !"
                    else:
                        temps_text = "Un Reiatsu 💠 est déjà apparu (lien indisponible)"
                else:
                    last_spawn = config.get("last_spawn_at")
                    delay = config.get("delay_minutes", 1800)
                    if last_spawn:
                        remaining = int(parser.parse(last_spawn).timestamp() + delay - time.time())
                        if remaining <= 0:
                            temps_text = "💠 Un Reiatsu peut apparaître à tout moment !"
                        else:
                            minutes, seconds = divmod(remaining, 60)
                            temps_text = f"**{minutes}m {seconds}s**"
                    else:
                        temps_text = "💠 Un Reiatsu peut apparaître à tout moment !"

        embed = discord.Embed(
            title="__**💠 Profil**__",
            description=f"**{user.display_name}** a actuellement : **{points}** points de Reiatsu\n"
                        f"• 🕵️ Cooldown vol : {cooldown_text}\n\n__**Classe**__\n{classe_text}\n\n"
                        f"__**Spawn du reiatsu**__\n• 📍 Lieu : {salon_text}\n• ⏳ Temps avant apparition : {temps_text}",
            color=discord.Color.purple()
        )
        embed.set_footer(text="Utilise les boutons ci-dessous pour interagir.")
        view = ReiatsuView(author, guild, spawn_link=spawn_link)

        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed, view=view)
        else:
            await safe_send(ctx_or_interaction, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Gestion des boutons
    # ────────────────────────────────────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id")
        if not custom_id:
            return
        user_id = str(interaction.user.id)

        # Vérification utilisateur
        if interaction.user != interaction.user:
            await interaction.response.send_message("❌ Tu ne peux pas utiliser ce bouton.", ephemeral=True)
            return

        if custom_id == "reiatsu:classement":
            await self.handle_classement(interaction)
        elif custom_id == "reiatsu:eveil":
            await self.handle_eveil(interaction)
        elif custom_id == "reiatsu:classe":
            await self.handle_classe(interaction)
        elif custom_id == "reiatsu:vol":
            await self.handle_vol(interaction)

    async def handle_classement(self, interaction: discord.Interaction):
        data = supabase.table("reiatsu").select("user_id, points").order("points", desc=True).limit(10).execute()
        if not data.data:
            return await interaction.response.send_message("Aucun classement disponible.", ephemeral=True)
        description = ""
        for i, entry in enumerate(data.data, start=1):
            member = interaction.guild.get_member(int(entry["user_id"])) if interaction.guild else None
            name = member.display_name if member else f"Utilisateur ({entry['user_id']})"
            description += f"**{i}. {name}** — {entry['points']} points\n"
        embed = discord.Embed(title="📊 Classement Reiatsu", description=description, color=discord.Color.purple())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def handle_eveil(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        data = supabase.table("reiatsu").select("points").eq("user_id", user_id).execute()
        if not data.data:
            return await interaction.response.send_message("❌ Pas de compte Reiatsu.", ephemeral=True)
        points = data.data[0]["points"]
        EVEIL_COST = 1
        if points < EVEIL_COST:
            return await interaction.response.send_message(f"⛔ Pas assez de points ({EVEIL_COST} requis).", ephemeral=True)

        view = View()
        for pouvoir in ["Shinigami", "Hollow", "Quincy", "Fullbring"]:
            view.add_item(Button(label=pouvoir, style=discord.ButtonStyle.primary, custom_id=f"eveil:{pouvoir}"))
        await interaction.response.send_message("Choisis ton pouvoir :", view=view, ephemeral=True)

    async def handle_classe(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        with open("data/classes.json", "r", encoding="utf-8") as f:
            CLASSES = json.load(f)
        options = [discord.SelectOption(label=f"{data.get('Symbole','🌀')} {classe}", description=data['Passive'][:100], value=classe) for classe, data in CLASSES.items()]
        select = Select(placeholder="Choisis ta classe", options=options, min_values=1, max_values=1)

        async def callback(i: discord.Interaction):
            classe = select.values[0]
            nouveau_cd = 19 if classe == "Voleur" else 24
            supabase.table("reiatsu").update({"classe": classe, "steal_cd": nouveau_cd}).eq("user_id", user_id).execute()
            symbole = CLASSES[classe].get("Symbole","🌀")
            embed = discord.Embed(title=f"✅ Classe choisie : {symbole} {classe}", color=discord.Color.green())
            await i.response.edit_message(embed=embed, view=None)

        select.callback = callback
        view = View()
        view.add_item(select)
        await interaction.response.send_message("Sélectionne ta classe :", view=view, ephemeral=True)

    async def handle_vol(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        guild = interaction.guild
        options = [discord.SelectOption(label=m.display_name, value=str(m.id)) for m in guild.members if not m.bot and m.id != interaction.user.id]
        if not options:
            return await interaction.response.send_message("Aucune cible disponible.", ephemeral=True)
        select = Select(placeholder="Choisis une cible à voler", options=options, min_values=1, max_values=1)

        async def callback(i: discord.Interaction):
            cible_id = select.values[0]
            voleur_data = supabase.table("reiatsu").select("*").eq("user_id", user_id).execute().data[0]
            cible_data = supabase.table("reiatsu").select("*").eq("user_id", cible_id).execute().data[0]
            voleur_classe = voleur_data.get("classe")
            voleur_cd = voleur_data.get("steal_cd", 24)
            now = datetime.utcnow()
            dernier_vol_str = voleur_data.get("last_steal_attempt")
            if dernier_vol_str:
                dernier_vol = datetime.fromisoformat(dernier_vol_str)
                prochain_vol = dernier_vol + timedelta(hours=voleur_cd)
                if now < prochain_vol:
                    restant = prochain_vol - now
                    j = restant.days
                    h, m = divmod(restant.seconds//60,60)
                    return await i.response.send_message(f"⏳ Attends {j}j {h}h{m}m avant de retenter.", ephemeral=True)
            montant = max(1, cible_data.get("points",0)//10)
            if voleur_classe=="Voleur" and random.random()<0.15:
                montant*=2
            succes = random.random() < (0.67 if voleur_classe=="Voleur" else 0.25)
            payload_voleur={"last_steal_attempt":now.isoformat()}
            if succes:
                payload_voleur["points"]=voleur_data.get("points",0)+montant
                supabase.table("reiatsu").update(payload_voleur).eq("user_id", user_id).execute()
                if cible_data.get("classe")=="Illusionniste" and random.random()<0.5:
                    await i.response.send_message(f"🩸 {interaction.user.mention} a volé {montant} points à {guild.get_member(int(cible_id)).mention}… mais c'était une illusion !", ephemeral=True)
                else:
                    supabase.table("reiatsu").update({"points":max(0,cible_data.get("points",0)-montant)}).eq("user_id",cible_id).execute()
                    await i.response.send_message(f"🩸 {interaction.user.mention} a réussi à voler {montant} points à {guild.get_member(int(cible_id)).mention} !", ephemeral=True)
            else:
                supabase.table("reiatsu").update(payload_voleur).eq("user_id", user_id).execute()
                await i.response.send_message(f"😵 {interaction.user.mention} a tenté de voler {guild.get_member(int(cible_id)).mention}… mais a échoué !", ephemeral=True)

        select.callback=callback
        view = View()
        view.add_item(select)
        await interaction.response.send_message("Choisis une cible :", view=view, ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commandes
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="reiatsu", description="💠 Affiche le score de Reiatsu d’un membre")
    @app_commands.describe(member="Membre dont vous voulez voir le Reiatsu")
    @app_commands.checks.cooldown(1, 3.0, key=lambda i: i.user.id)
    async def slash_reiatsu(self, interaction: discord.Interaction, member: discord.Member = None):
        try:
            await self._send_profile(interaction, interaction.user, interaction.guild, member)
        except Exception as e:
            print(f"[ERREUR /reiatsu] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="reiatsu", aliases=["rts"])
    @commands.cooldown(1, 3.0, commands.BucketType.user)
    async def prefix_reiatsu(self, ctx: commands.Context, member: discord.Member = None):
        try:
            await ctx.message.delete()
        except:
            pass
        await self._send_profile(ctx.channel, ctx.author, ctx.guild, member)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ReiatsuCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
