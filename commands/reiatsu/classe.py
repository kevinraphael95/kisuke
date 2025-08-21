# ────────────────────────────────────────────────────────────────────────────────
# 📌 choisir_classe.py — Commande interactive !classe
# Objectif : Permettre aux joueurs de choisir leur classe Reiatsu via un menu déroulant
# Catégorie : Reiatsu
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View
from supabase import create_client, Client
import os
import json

from utils.discord_utils import safe_send, safe_respond  # <-- import fonctions anti 429

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Configuration Supabase
# ────────────────────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ────────────────────────────────────────────────────────────────────────────────
# 📊 Données des classes Reiatsu
# ────────────────────────────────────────────────────────────────────────────────
with open("data/classes.json", "r", encoding="utf-8") as f:
    CLASSES = json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Vue du menu de sélection de classe
# ────────────────────────────────────────────────────────────────────────────────
class ClasseSelect(discord.ui.Select):
    def __init__(self, user_id):
        self.user_id = user_id

        options = [
            discord.SelectOption(
                label=f"{data.get('Symbole', '🌀')} {classe}",
                description=data["Passive"][:100],
                value=classe
            )
            for classe, data in CLASSES.items()
        ]

        super().__init__(
            placeholder="Choisis ta classe Reiatsu",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await safe_respond(
                interaction,
                "❌ Tu ne peux pas choisir une classe pour un autre joueur.",
                ephemeral=True
            )
            return

        classe = self.values[0]
        user_id = str(interaction.user.id)

        try:
            # Ajuste le cooldown selon la classe choisie
            nouveau_cd = 19 if classe == "Voleur" else 24

            supabase.table("reiatsu").update({
                "classe": classe,
                "steal_cd": nouveau_cd
            }).eq("user_id", user_id).execute()

            symbole = CLASSES[classe].get("Symbole", "🌀")

            embed = discord.Embed(
                title=f"✅ Classe choisie : {symbole} {classe}",
                description=(
                    f"**Passive** : {CLASSES[classe]['Passive']}\n"
                    f"**Active** : {CLASSES[classe]['Active']}"
                ),
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=None)

        except Exception as e:
            await safe_respond(interaction, f"❌ Erreur lors de l'enregistrement : {e}", ephemeral=True)


class ClasseSelectView(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.add_item(ClasseSelect(user_id))

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ChoisirClasse(commands.Cog):
    """
    Commande !classe — Choisir sa classe Reiatsu
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="classe",
        help="Choisir sa classe Reiatsu",
        description="Affiche un menu interactif pour choisir sa spécialisation Reiatsu."
    )
    async def classe(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🎭 Choisis ta classe Reiatsu",
            description=(
                "Sélectionne une classe dans le menu déroulant ci-dessous. "
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

        view = ClasseSelectView(ctx.author.id)
        await safe_send(ctx.channel, embed=embed, view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ChoisirClasse(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)


