# ────────────────────────────────────────────────────────────────────────────────
# 📌 course_tortues.py — Commande interactive !tortues
# Objectif : Mini-jeu simple de course de tortues avec mise et boutons emoji
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import random
from utils.discord_utils import safe_send, safe_edit  # ✅ Utilisation des safe_

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Constantes et emojis
# ────────────────────────────────────────────────────────────────────────────────
TOUR_MAX = 20  # Nb max de tours pour la course
DISTANCE = 15  # Distance à parcourir (nombre d’emoji 🐢)

EMOJI_TORTUES = ["🐢", "🐢", "🐢", "🐢"]
EMOJI_LIGNE_ARRIVEE = "🏁"
EMOJI_PISTE = "·"  # Point pour la piste

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue avec boutons pour choisir sa tortue
# ────────────────────────────────────────────────────────────────────────────────
class ChoixTortueView(View):
    def __init__(self, bot):
        super().__init__(timeout=30)
        self.bot = bot
        self.choix = None
        # Ajout des 4 boutons pour choix des tortues
        for i in range(4):
            self.add_item(ChoixTortueButton(i))

    async def on_timeout(self):
        self.clear_items()

class ChoixTortueButton(Button):
    def __init__(self, index):
        super().__init__(label=f"Tortue {index + 1}", style=discord.ButtonStyle.primary)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        self.view.choix = self.index
        self.view.stop()
        await interaction.response.defer()

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Fonction d’affichage de la course dans un embed
# ────────────────────────────────────────────────────────────────────────────────
def afficher_course(pos):
    lignes = []
    for i, p in enumerate(pos):
        piste = EMOJI_PISTE * p
        espace = EMOJI_PISTE * (DISTANCE - p)
        lignes.append(f"Tortue {i+1} {EMOJI_TORTUES[i]} : {piste}{EMOJI_TORTUES[i]}{espace}{EMOJI_LIGNE_ARRIVEE}")
    return "\n".join(lignes)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CourseTortues(commands.Cog):
    """
    Commande !tortues — Mini-jeu de course de tortues interactive
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tortues", help="Participe à une course de tortues !")
    async def tortues(self, ctx: commands.Context):
        """Lance une course de tortues interactive avec choix et course."""

        view = ChoixTortueView(self.bot)
        try:
            msg = await safe_send(ctx.channel, "Choisis ta tortue pour la course :", view=view)
            await view.wait()
            if view.choix is None:
                await safe_edit(msg, content="⏰ Temps écoulé, aucune tortue sélectionnée.", view=None)
                return

            joueur = view.choix
            positions = [0, 0, 0, 0]

            embed = discord.Embed(
                title="🏁 Course de tortues 🐢",
                description=afficher_course(positions),
                color=discord.Color.green()
            )
            await safe_edit(msg, content=None, embed=embed, view=None)

            gagnant = None

            # Boucle de la course
            for tour in range(TOUR_MAX):
                for i in range(4):
                    positions[i] += random.choice([0, 1])
                    if positions[i] > DISTANCE:
                        positions[i] = DISTANCE

                embed.description = afficher_course(positions)
                await safe_edit(msg, embed=embed)

                for i, pos in enumerate(positions):
                    if pos >= DISTANCE:
                        gagnant = i
                        break

                if gagnant is not None:
                    break

                await asyncio.sleep(1)

            # Résultat
            if gagnant == joueur:
                msg_fin = "🎉 Félicitations ! Ta tortue a gagné la course !"
            else:
                msg_fin = f"😞 Dommage, la tortue {gagnant + 1} a gagné cette fois."

            embed.description += f"\n\n**{msg_fin}**"
            await safe_edit(msg, embed=embed)

        except Exception as e:
            print(f"[ERREUR !tortues] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue lors de la course.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CourseTortues(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
