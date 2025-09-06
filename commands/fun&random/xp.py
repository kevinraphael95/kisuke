# ────────────────────────────────────────────────────────────────────────────────
# 📌 xp_simulator.py — Commande interactive style Windows XP sur Discord
# Objectif : Simuler le bureau, la barre des tâches, le menu démarrer et les applis
# Catégorie : Jeu / Fun
# Accès : Tous
# Cooldown : 1 utilisation / 15 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput

# ────────────────────────────────────────────────────────────────────────────────
# 🖥️ Bureau XP avec barre des tâches et menu démarrer
# ────────────────────────────────────────────────────────────────────────────────
class XPDesktopView(View):
    def __init__(self):
        super().__init__(timeout=None)
        # Bouton Démarrer
        self.add_item(Button(label="Démarrer", style=discord.ButtonStyle.green, custom_id="start_menu"))
        # Icônes bureau
        self.add_item(Button(label="Notepad", style=discord.ButtonStyle.blurple, custom_id="notepad"))
        self.add_item(Button(label="Paint", style=discord.ButtonStyle.blurple, custom_id="paint"))
        # Horloge barre des tâches
        self.add_item(Button(label="Horloge", style=discord.ButtonStyle.gray, custom_id="clock"))

    @discord.ui.button(label="Démarrer", style=discord.ButtonStyle.green, custom_id="start_menu")
    async def start_menu(self, interaction: discord.Interaction, button: Button):
        menu = StartMenuView()
        await interaction.response.send_message("💻 Menu Démarrer", view=menu, ephemeral=True)

    @discord.ui.button(label="Notepad", style=discord.ButtonStyle.blurple, custom_id="notepad")
    async def open_notepad(self, interaction: discord.Interaction, button: Button):
        modal = NotepadModal(title="Notepad")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Paint", style=discord.ButtonStyle.blurple, custom_id="paint")
    async def open_paint(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🖌️ Paint simulé : dessinez avec des emojis !", ephemeral=True)

    @discord.ui.button(label="Horloge", style=discord.ButtonStyle.gray, custom_id="clock")
    async def show_clock(self, interaction: discord.Interaction, button: Button):
        import datetime
        now = datetime.datetime.now().strftime('%H:%M:%S')
        await interaction.response.send_message(f"⏰ Heure actuelle : {now}", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 📝 Notepad Modal
# ────────────────────────────────────────────────────────────────────────────────
class NotepadModal(Modal):
    def __init__(self, title):
        super().__init__(title=title)
        self.text_input = TextInput(label="Écris ici", style=discord.TextStyle.paragraph, placeholder="Tape ton texte...", required=False)
        self.add_item(self.text_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"📄 Contenu enregistré :\n{self.text_input.value}", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🍀 Menu Démarrer
# ────────────────────────────────────────────────────────────────────────────────
class StartMenuView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Notepad", style=discord.ButtonStyle.blurple, custom_id="start_notepad"))
        self.add_item(Button(label="Paint", style=discord.ButtonStyle.blurple, custom_id="start_paint"))
        self.add_item(Button(label="Fermer session", style=discord.ButtonStyle.red, custom_id="logout"))

    @discord.ui.button(label="Notepad", style=discord.ButtonStyle.blurple, custom_id="start_notepad")
    async def start_notepad(self, interaction: discord.Interaction, button: Button):
        modal = NotepadModal(title="Notepad")
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Paint", style=discord.ButtonStyle.blurple, custom_id="start_paint")
    async def start_paint(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🖌️ Paint simulé : dessinez avec des emojis !", ephemeral=True)

    @discord.ui.button(label="Fermer session", style=discord.ButtonStyle.red, custom_id="logout")
    async def logout(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("🔴 Session fermée. À bientôt !", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class XPDiscord(commands.Cog):
    """Simulateur Windows XP sur Discord"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="xp", description="Simule le bureau Windows XP")
    @app_commands.checks.cooldown(1, 15.0, key=lambda i: i.user.id)
    async def slash_xp(self, interaction: discord.Interaction):
        try:
            view = XPDesktopView()
            await interaction.response.send_message("🖥️ Bienvenue sur Windows XP !", view=view)
        except Exception as e:
            print(f"[ERREUR /xp] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    @commands.command(name="xp")
    @commands.cooldown(1, 15.0, commands.BucketType.user)
    async def prefix_xp(self, ctx: commands.Context):
        try:
            view = XPDesktopView()
            await ctx.send("🖥️ Bienvenue sur Windows XP !", view=view)
        except Exception as e:
            print(f"[ERREUR !xp] {e}")
            await ctx.send("❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = XPDiscord(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Fun"
    await bot.add_cog(cog)
