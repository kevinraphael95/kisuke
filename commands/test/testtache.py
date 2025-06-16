# ────────────────────────────────────────────────────────────────────────────────
# 📌 test_taches.py — Commande interactive !testtache
# Objectif : Tester toutes les tâches interactives du mode Hollow Among Us
# Catégorie : Bleach / Mini-jeux
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Select
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Tâches disponibles
# ────────────────────────────────────────────────────────────────────────────────
TACHES = {
    "Quiz Bleach": "quiz",
    "Code Hollow": "code",
    "Séquence emoji": "emoji",
    "Réflexe rapide": "reflexe"
}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Menu de sélection des tâches
# ────────────────────────────────────────────────────────────────────────────────
class TacheSelectView(View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.bot = bot
        self.add_item(TacheSelect(self))

class TacheSelect(Select):
    def __init__(self, parent_view: TacheSelectView):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=label, value=value) for label, value in TACHES.items()]
        super().__init__(placeholder="Choisis une tâche à tester", options=options)

    async def callback(self, interaction: discord.Interaction):
        task_type = self.values[0]
        await interaction.response.edit_message(content=f"🔧 Tâche sélectionnée : `{task_type}`", view=None)

        if task_type == "quiz":
            await lancer_quiz(interaction)
        elif task_type == "code":
            await lancer_code(interaction)
        elif task_type == "emoji":
            await lancer_emoji(interaction)
        elif task_type == "reflexe":
            await lancer_reflexe(interaction)

# 🔹 Fonctions de tâche (exemples de mini-jeux)
async def lancer_quiz(interaction):
    question = "Quel capitaine a pour zanpakutō Senbonzakura?"
    bonne_reponse = "Byakuya"

    await interaction.followup.send(f"❓ {question}\nRéponds avec `!rep <ta réponse>`.")

    def check(m):
        return m.channel == interaction.channel and m.content.startswith("!rep")

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=15)
        reponse = msg.content[5:].strip().lower()
        if reponse == bonne_reponse.lower():
            await interaction.followup.send(f"✅ Bonne réponse {msg.author.mention} !")
        else:
            await interaction.followup.send(f"❌ Mauvaise réponse {msg.author.mention} !")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Temps écoulé, personne n'a répondu.")

async def lancer_code(interaction):
    mot_code = "H_L_OW"
    await interaction.followup.send(f"🔐 Devine le mot : `{mot_code}` — Réponds avec `!rep <mot>`")

    def check(m):
        return m.channel == interaction.channel and m.content.startswith("!rep")

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=10)
        if msg.content[5:].strip().lower() == "hollow":
            await interaction.followup.send(f"✅ Bien joué {msg.author.mention}, c'était `HOLLOW` !")
        else:
            await interaction.followup.send(f"❌ Mauvais mot {msg.author.mention}.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Trop tard.")

async def lancer_emoji(interaction):
    sequence = ["🔥", "💀", "🌀"]
    await interaction.followup.send(f"🔁 Reproduis cette séquence : {' '.join(sequence)}\nRéponds avec `!rep 🔥 💀 🌀` exactement !")

    def check(m):
        return m.channel == interaction.channel and m.content.startswith("!rep")

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=12)
        if msg.content[5:].strip() == " ".join(sequence):
            await interaction.followup.send(f"✅ Bonne séquence, {msg.author.mention} !")
        else:
            await interaction.followup.send("❌ Séquence incorrecte.")
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Temps écoulé.")

async def lancer_reflexe(interaction):
    await interaction.followup.send("⚡ Tape `!vite` en moins de 5 secondes pour réussir !")

    def check(m):
        return m.channel == interaction.channel and m.content.strip() == "!vite"

    try:
        msg = await interaction.client.wait_for("message", check=check, timeout=5)
        await interaction.followup.send(f"✅ Rapidité confirmée, {msg.author.mention} !")
    except asyncio.TimeoutError:
        await interaction.followup.send("❌ Trop lent !")

# 🧠 Cog principal
class TestTache(commands.Cog):
    """
    Commande !testtache — Teste les différentes tâches du mode Hollow
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="testtache",
        help="Test des tâches interactives.",
        description="Testez les mini-jeux de tâches inspirées d'Among Us Hollow."
    )
    async def testtache(self, ctx: commands.Context):
        try:
            view = TacheSelectView(self.bot)
            await ctx.send("🧪 Choisis une tâche à tester :", view=view)
        except Exception as e:
            print(f"[ERREUR testtache] {e}")
            await ctx.send("❌ Erreur lors de l'affichage des tâches.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TestTache(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
