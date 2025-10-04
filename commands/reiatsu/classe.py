# ────────────────────────────────────────────────────────────────────────────────
# 📌 choisir_classe.py — Commande interactive !classe /classe
# Objectif : Permet aux joueurs de choisir leur classe Reiatsu via des boutons
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
from discord.ui import View
import os
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

# ────────────────────────────────────────────────────────────────
# 📊 Données des classes Reiatsu depuis reiatsu_config.json
# ────────────────────────────────────────────────────────────────
with open("data/reiatsu_config.json", "r", encoding="utf-8") as f:
    config = json.load(f)
CLASSES = config.get("CLASSES", {})

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Boutons interactifs de sélection de classe
# ────────────────────────────────────────────────────────────────────────────────
class ClasseButton(discord.ui.Button):
    def __init__(self, user_id: int, classe: str, data: dict):
        self.user_id = user_id
        self.classe = classe
        self.data = data
        label = f"{data.get('Symbole', '🌀')} {classe}"
        super().__init__(label=label, style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await safe_respond(interaction, "❌ Tu ne peux pas choisir une classe pour un autre joueur.", ephemeral=True)
            return

        try:
            nouveau_cd = 19 if self.classe == "Voleur" else 24
            supabase.table("reiatsu").update({
                "classe": self.classe,
                "steal_cd": nouveau_cd
            }).eq("user_id", str(interaction.user.id)).execute()

            symbole = self.data.get("Symbole", "🌀")
            embed = discord.Embed(
                title=f"✅ Classe choisie : {symbole} {self.classe}",
                description=f"**Passive** : {self.data['Passive']}\n**Active** : {self.data['Active']}",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=None)
        except Exception as e:
            await safe_respond(interaction, f"❌ Erreur lors de l'enregistrement : {e}", ephemeral=True)


class ClasseButtonsView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        for classe, data in CLASSES.items():
            self.add_item(ClasseButton(user_id, classe, data))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ChoisirClasse(commands.Cog):
    """
    Commande !classe ou /classe — Choisir sa classe Reiatsu via des boutons
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_menu(self, channel: discord.abc.Messageable, user_id: int):
        embed = discord.Embed(
            title="🎭 Choisis ta classe Reiatsu",
            description=(
                "Clique sur un bouton ci-dessous pour choisir ta classe.\n"
                "Chaque classe possède une compétence passive et une active.\n\n"
                "👉 Si tu n’as jamais choisi de classe, tu es **Travailleur** par défaut."
            ),
            color=discord.Color.purple()
        )
        for nom, details in CLASSES.items():
            symbole = details.get("Symbole", "🌀")
            embed.add_field(
                name=f"{symbole} {nom}",
                value=f"**Passive :** {details['Passive']}\n**Active :** {details['Active']}",
                inline=False
            )
        view = ClasseButtonsView(user_id)
        await safe_send(channel, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande préfixe
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="classe", help="Choisir sa classe Reiatsu")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def classe_prefix(self, ctx: commands.Context):
        await self._send_menu(ctx.channel, ctx.author.id)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande slash
    # ────────────────────────────────────────────────────────────────────────────
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
