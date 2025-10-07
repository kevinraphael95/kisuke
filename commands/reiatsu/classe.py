# ────────────────────────────────────────────────────────────────────────────────
# 📌 choisir_classe.py — Commande interactive !classe /classe
# Objectif : Permet aux joueurs de choisir leur classe Reiatsu via des boutons et pagination
# Catégorie : Reiatsu
# Accès : Public
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime, timedelta, timezone
import json
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_respond, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Tables utilisées
# ────────────────────────────────────────────────────────────────────────────────
TABLES = {
    "reiatsu": {
        "description": "Contient les informations Reiatsu des joueurs, y compris leur classe et le cooldown associé.",
        "colonnes": {
            "user_id": "BIGINT — Identifiant Discord unique de l'utilisateur (clé primaire)",
            "username": "TEXT — Nom d'utilisateur Discord",
            "points": "INTEGER — Score Reiatsu du joueur",
            "classe": "TEXT — Classe actuellement sélectionnée par le joueur",
            "steal_cd": "INTEGER — Cooldown du vol (en heures, varie selon la classe)",
            "last_steal_attempt": "TIMESTAMP — Date et heure de la dernière tentative de vol",
            "last_skilled_at": "TIMESTAMP — Date et heure de la dernière utilisation de compétence active",
            "active_skill": "BOOLEAN — Indique si la compétence active est en cours d'utilisation",
            "fake_spawn_id": "TEXT — Identifiant temporaire d’un spawn simulé (optionnel)"
        }
    }
}

# ────────────────────────────────────────────────
# 📊 Données des classes Reiatsu depuis reiatsu_config.json
# ────────────────────────────────────────────────
with open("data/reiatsu_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
CLASSES = list(config.get("CLASSES", {}).items())

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Pagination + Choix de classe
# ────────────────────────────────────────────────────────────────────────────────
class ClassePageView(View):
    def __init__(self, user_id: int, index: int = 0):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.index = index
        self.total = len(CLASSES)
        self.update_buttons()

    def update_buttons(self):
        self.clear_items()

        # Boutons de navigation
        prev_btn = Button(label="⬅️ Précédent", style=discord.ButtonStyle.secondary)
        prev_btn.callback = self.prev_page
        self.add_item(prev_btn)

        next_btn = Button(label="➡️ Suivant", style=discord.ButtonStyle.secondary)
        next_btn.callback = self.next_page
        self.add_item(next_btn)

        # Bouton choisir
        choose_btn = Button(label="✅ Choisir cette classe", style=discord.ButtonStyle.success)
        choose_btn.callback = self.choose_class
        self.add_item(choose_btn)

    async def on_timeout(self):
        """Désactive automatiquement les boutons après le temps limite."""
        for item in self.children:
            item.disabled = True
        if hasattr(self, "message"):
            try:
                await safe_edit(self.message, view=self)
            except:
                pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await safe_respond(interaction, "❌ Tu ne peux pas interagir avec le menu d’un autre joueur.", ephemeral=True)
            return False
        return True

    # ──────────────────────────────
    # Callbacks
    # ──────────────────────────────
    async def prev_page(self, interaction: discord.Interaction):
        self.index = (self.index - 1) % self.total
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def next_page(self, interaction: discord.Interaction):
        self.index = (self.index + 1) % self.total
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def choose_class(self, interaction: discord.Interaction):
        nom, data = CLASSES[self.index]

        # 🔒 Vérification du cooldown ou de l'utilisation du skill
        try:
            res = supabase.table("reiatsu").select("last_skilled_at, active_skill").eq("user_id", str(self.user_id)).execute()
            user_data = res.data[0] if res.data else {}

            last_skill = user_data.get("last_skilled_at")
            active_skill = user_data.get("active_skill", False)

            # ───────────── Skill actif
            if active_skill:
                embed = discord.Embed(
                    title="🌀 Skill en cours d’utilisation",
                    description="Tu ne peux pas changer de classe tant que ton **skill actif** est en cours.",
                    color=discord.Color.orange()
                )
                embed.set_footer(text="Attends la fin de ton skill avant de retenter.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # ───────────── Skill en cooldown
            if last_skill:
                last_dt = datetime.fromisoformat(last_skill.replace("Z", "+00:00"))
                cooldown_hours = data.get("Cooldown", 12)
                restant = (last_dt + timedelta(hours=cooldown_hours)) - datetime.now(timezone.utc)
                if restant.total_seconds() > 0:
                    h, m = divmod(int(restant.total_seconds() // 60), 60)
                    temps = f"{restant.days}j {h}h{m}m" if restant.days else f"{h}h{m}m"
                    embed = discord.Embed(
                        title="⏳ Skill en cooldown",
                        description=f"Ton **skill** est encore en recharge pendant `{temps}`.\nTu pourras changer de classe une fois le cooldown terminé.",
                        color=discord.Color.red()
                    )
                    embed.set_footer(text="Patience, le Reiatsu se régénère…")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
        except Exception as e:
            await safe_respond(interaction, f"❌ Erreur lors de la vérification du cooldown : {e}", ephemeral=True)
            return

        # ✅ Application du changement
        try:
            nouveau_cd = 19 if nom == "Voleur" else 24
            supabase.table("reiatsu").update({
                "classe": nom,
                "steal_cd": nouveau_cd
            }).eq("user_id", str(self.user_id)).execute()

            symbole = data.get("Symbole", "🌀")
            embed = discord.Embed(
                title=f"✅ Classe choisie : {symbole} {nom}",
                description=f"**Passive** : {data['Passive']}\n**Active** : {data['Active']}",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            await safe_respond(interaction, f"❌ Erreur lors de l'enregistrement : {e}", ephemeral=True)

    # ──────────────────────────────
    # Embed affichage
    # ──────────────────────────────
    def get_embed(self):
        nom, data = CLASSES[self.index]
        symbole = data.get("Symbole", "🌀")
        embed = discord.Embed(
            title=f"🎭 Classe {self.index + 1}/{self.total} — {symbole} {nom}",
            description=f"**Passif** : {data['Passive']}\n**Skill** : {data['Active']}",
            color=discord.Color.purple()
        )
        embed.set_footer(text="Utilise les flèches pour naviguer et ✅ pour choisir cette classe")
        return embed

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ChoisirClasse(commands.Cog):
    """
    Commande !classe ou /classe — Choisir sa classe Reiatsu via pagination et boutons
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_menu(self, channel: discord.abc.Messageable, user_id: int):
        view = ClassePageView(user_id)
        embed = view.get_embed()
        message = await safe_send(channel, embed=embed, view=view)
        view.message = message

    # ────────────────────────────────────────────────────────────
    # 🔹 Commande préfixe
    # ────────────────────────────────────────────────────────────
    @commands.command(name="classe", help="Choisir sa classe Reiatsu")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def classe_prefix(self, ctx: commands.Context):
        await self._send_menu(ctx.channel, ctx.author.id)

    # ────────────────────────────────────────────────────────────
    # 🔹 Commande slash
    # ────────────────────────────────────────────────────────────
    @app_commands.command(name="classe", description="Choisir sa classe Reiatsu")
    async def classe_slash(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._send_menu(interaction.channel, interaction.user.id)
        try:
            await interaction.delete_original_response()
        except discord.Forbidden:
            pass

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ChoisirClasse(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
