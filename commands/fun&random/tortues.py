# ────────────────────────────────────────────────────────────────────────────────
# 📌 course_tortues.py — Course de tortues multijoueur avec noms aléatoires
# Objectif : Mini-jeu interactif où plusieurs joueurs choisissent une tortue 🐢
# Catégorie : Fun
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
import asyncio
import random
from utils.discord_utils import safe_send, safe_edit, safe_respond  # ✅ Utilitaires sécurisés

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Constantes
# ────────────────────────────────────────────────────────────────────────────────
TOUR_MAX = 20
DISTANCE = 15
EMOJI_TORTUES = ["🐢", "🐢", "🐢", "🐢"]
EMOJI_LIGNE_ARRIVEE = "🏁"
EMOJI_PISTE = "·"

NOMS_TORTUES = [
    "Turbo", "Carapace Jr.", "Speedy", "Donatello",
    "Flashshell", "Shelldon", "Rapido", "Lentix"
]

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 Vue pour choisir la tortue
# ────────────────────────────────────────────────────────────────────────────────
class ChoixTortueView(View):
    def __init__(self, tortues):
        super().__init__(timeout=30)
        self.tortues = tortues  # Liste des noms
        self.choix = {}  # {user_id: index}
        for i, nom in enumerate(tortues):
            self.add_item(ChoixTortueButton(i, nom))

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

class ChoixTortueButton(Button):
    def __init__(self, index, nom):
        super().__init__(label=f"{nom}", style=discord.ButtonStyle.primary)
        self.index = index
        self.nom = nom

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        view = self.view

        # Empêche un utilisateur de choisir plusieurs fois
        if user.id in view.choix:
            await interaction.response.send_message(
                f"🚫 Tu as déjà choisi la tortue **{view.tortues[view.choix[user.id]]}** !",
                ephemeral=True
            )
            return

        view.choix[user.id] = self.index
        await interaction.response.send_message(
            f"✅ {user.mention} a choisi la tortue **{self.nom}** !",
            ephemeral=True
        )

# ────────────────────────────────────────────────────────────────────────────────
# 🐢 Fonction d’affichage de la course
# ────────────────────────────────────────────────────────────────────────────────
def afficher_course(positions, tortues):
    lignes = []
    for i, p in enumerate(positions):
        piste = EMOJI_PISTE * p
        espace = EMOJI_PISTE * (DISTANCE - p)
        # Le nom après le drapeau
        lignes.append(
            f"{EMOJI_TORTUES[i]} : {piste}{EMOJI_TORTUES[i]}{espace}{EMOJI_LIGNE_ARRIVEE} **{tortues[i]}**"
        )
    return "\n".join(lignes)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CourseTortues(commands.Cog):
    """Commande /tortues — Course de tortues multijoueur avec noms aléatoires 🐢"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="tortues",
        description="Participe à une course de tortues avec tes amis ! 🐢"
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def slash_tortues(self, interaction: discord.Interaction):
        await self.lancer_course(interaction=interaction)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="tortues", help="Participe à une course de tortues avec tes amis ! 🐢")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_tortues(self, ctx: commands.Context):
        await self.lancer_course(ctx=ctx)

    # ────────────────────────────────────────────────────────────────────────────
    # ⚙️ Fonction principale
    # ────────────────────────────────────────────────────────────────────────────
    async def lancer_course(self, ctx: commands.Context = None, interaction: discord.Interaction = None):
        # Sélection de 4 noms aléatoires uniques
        tortues = random.sample(NOMS_TORTUES, 4)
        view = ChoixTortueView(tortues)

        description = "\n".join(
            [f"{EMOJI_TORTUES[i]} **{nom}**" for i, nom in enumerate(tortues)]
        )

        if interaction:
            msg = await safe_respond(interaction, f"🎲 Choisis ta tortue :\n\n{description}", view=view)
        else:
            msg = await safe_send(ctx.channel, f"🎲 Choisis ta tortue :\n\n{description}", view=view)

        await view.wait()

        if not view.choix:
            await safe_edit(msg, content="⏰ Personne n’a choisi de tortue...", view=None)
            return

        # Début de la course
        positions = [0, 0, 0, 0]
        embed = discord.Embed(
            title="🏁 Course de tortues 🐢",
            description=afficher_course(positions, tortues),
            color=discord.Color.green()
        )
        await safe_edit(msg, content=None, embed=embed, view=None)

        await asyncio.sleep(2)

        gagnant = None
        for tour in range(TOUR_MAX):
            for i in range(4):
                positions[i] += random.choice([0, 1, 1, 2])
                positions[i] = min(positions[i], DISTANCE)

            embed.description = afficher_course(positions, tortues)
            embed.set_footer(text=f"Tour {tour + 1}/{TOUR_MAX}")
            await safe_edit(msg, embed=embed)

            for i, pos in enumerate(positions):
                if pos >= DISTANCE:
                    gagnant = i
                    break
            if gagnant is not None:
                break

            await asyncio.sleep(1)

        # Liste des gagnants
        gagnants = [user_id for user_id, tortue in view.choix.items() if tortue == gagnant]

        if gagnants:
            noms = ", ".join(f"<@{uid}>" for uid in gagnants)
            texte = f"🎉 La tortue **{tortues[gagnant]}** a gagné ! Félicitations à {noms} !"
        else:
            texte = f"🐢 La tortue **{tortues[gagnant]}** a gagné, mais personne ne l’avait choisie !"

        embed.description += f"\n\n**{texte}**"
        await safe_edit(msg, embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CourseTortues(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun&Random"
    await bot.add_cog(cog)
