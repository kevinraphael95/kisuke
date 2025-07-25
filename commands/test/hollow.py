# ────────────────────────────────────────────────────────────────────────────────
# 📌 hollow.py — Commande interactive !hollow
# Objectif : Faire apparaître un Hollow, le joueur peut l’attaquer en dépensant 50 reiatsu
#           et doit accomplir 3 tâches pour le vaincre.
# Catégorie : Hollow
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import os
import traceback
import random
from utils.discord_utils import safe_send
from supabase_client import supabase

# Import des tâches (elles retournent un booléen True/False)
from test_taches import (
    lancer_emoji, lancer_reflexe, lancer_fleche,
    lancer_infusion, lancer_emoji9, lancer_bmoji
)

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Constantes
# ────────────────────────────────────────────────────────────────────────────────
HOLLOW_IMAGE_PATH = os.path.join("data", "hollows", "hollow0.jpg")
REIATSU_COST = 50

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Fonctions utilitaires de tâche
# ────────────────────────────────────────────────────────────────────────────────
TACHES_DISPONIBLES = [
    ("Séquence emoji", lancer_emoji),
    ("Réflexe rapide", lancer_reflexe),
    ("Séquence fléchée", lancer_fleche),
    ("Infusion Reiatsu", lancer_infusion),
    ("Emoji suspects", lancer_emoji9),
    ("Devine le perso (bmoji)", lancer_bmoji),
]

async def lancer_3_taches_différentes(interaction: discord.Interaction) -> bool:
    """
    Lance 3 tâches différentes au hasard et renvoie True si toutes sont réussies.
    """
    # Choix de 3 tâches distinctes
    selections = random.sample(TACHES_DISPONIBLES, 3)
    for i, (nom, fonction) in enumerate(selections, start=1):
        # Indication de la tâche
        await interaction.followup.send(f"🧪 Épreuve {i}/3 : **{nom}**", ephemeral=True)
        try:
            # Exécution et récupération du résultat
            resultat = await fonction(interaction)
        except Exception:
            traceback.print_exc()
            resultat = False

        if not resultat:
            # échec immédiat
            await interaction.followup.send("❌ Échec d’une épreuve. Le Hollow t’a vaincu...", ephemeral=True)
            return False

    # succès de toutes les tâches
    await interaction.followup.send("✅ Tu as réussi les 3 épreuves !", ephemeral=True)
    return True

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Vue avec bouton d’attaque
# ────────────────────────────────────────────────────────────────────────────────
class HollowView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.attacked = False
        self.message = None  # Définie après envoi initial

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass  # message supprimé ou autre

    @discord.ui.button(label=f"Attaquer ({REIATSU_COST} reiatsu)", style=discord.ButtonStyle.red)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Vérification de l’utilisateur
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Ce bouton n’est pas pour toi.", ephemeral=True)
            return
        if self.attacked:
            await interaction.response.send_message("⚠️ Tu as déjà attaqué ce Hollow.", ephemeral=True)
            return

        # Début de traitement
        await interaction.response.defer(thinking=True)
        user_id = str(interaction.user.id)

        try:
            # 1️⃣ Vérification des points
            resp = supabase.table("reiatsu").select("points").eq("user_id", user_id).execute()
            if not resp.data:
                await interaction.followup.send("❌ Tu n’as pas de Reiatsu enregistré.", ephemeral=True)
                return
            points = resp.data[0].get("points", 0)
            if points < REIATSU_COST:
                await interaction.followup.send(f"❌ Il te faut {REIATSU_COST} reiatsu pour attaquer.", ephemeral=True)
                return

            # 2️⃣ Déduction de reiatsu
            new_points = points - REIATSU_COST
            upd = supabase.table("reiatsu").update({"points": new_points}).eq("user_id", user_id).execute()
            if not upd.data:
                await interaction.followup.send("⚠️ Erreur lors de la mise à jour de ton reiatsu.", ephemeral=True)
                return

            self.attacked = True
            await interaction.followup.send(
                f"💥 {interaction.user.display_name} engage le combat contre le Hollow !", ephemeral=True
            )

            # 3️⃣ Lancement des 3 tâches
            victoire = await lancer_3_taches_différentes(interaction)

            # 4️⃣ Message final
            if victoire:
                await interaction.followup.send(
                    f"🎉 Bravo {interaction.user.display_name}, tu as vaincu le Hollow !", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"💀 Le Hollow t’a submergé. Retente ta chance plus tard !", ephemeral=True
                )

            # 5️⃣ Désactivation du bouton
            for child in self.children:
                child.disabled = True
            if self.message:
                await self.message.edit(view=self)

        except Exception:
            print("[ERREUR SUPABASE OU INTERACTION] attack_button :")
            traceback.print_exc()
            await interaction.followup.send("⚠️ Une erreur inattendue est survenue.", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal — HollowCommand
# ────────────────────────────────────────────────────────────────────────────────
class HollowCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="hollow",
        help="Fais apparaître un Hollow à attaquer en dépensant 50 reiatsu."
    )
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def hollow(self, ctx: commands.Context):
        if not os.path.isfile(HOLLOW_IMAGE_PATH):
            await safe_send(ctx, "❌ Image du Hollow introuvable.")
            return

        file = discord.File(HOLLOW_IMAGE_PATH, filename="hollow.jpg")
        embed = discord.Embed(
            title="👹 Un Hollow est apparu !",
            description=f"Attaque-le en dépensant {REIATSU_COST} Reiatsu et réussis 3 tâches pour le vaincre.",
            color=discord.Color.dark_red()
        )
        embed.set_image(url="attachment://hollow.jpg")
        embed.set_footer(text="Tu as 60 secondes pour cliquer sur Attaquer.")

        view = HollowView(author_id=ctx.author.id)
        message = await ctx.send(embed=embed, file=file, view=view)
        view.message = message  # Enregistrement du message pour la vue

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HollowCommand(bot)
    for command in cog.get_commands():
        command.category = "Hollow"
    await bot.add_cog(cog)
