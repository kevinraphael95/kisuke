# ────────────────────────────────────────────────────────────────────────────────
# 📌 fakenitro_proof.py — Commande interactive /proof et !proof
# Objectif : Générer un faux message Discord Nitro ultra réaliste (image HTML→PNG)
# Catégorie : Autre
# Accès : Admin (optionnel) / Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import datetime, random, traceback, json, os, base64
from html2image import Html2Image

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Configuration
# ────────────────────────────────────────────────────────────────────────────────
hti = Html2Image(custom_flags=["--default-background-color=ffffff"])
hti.browser.use_new_headless = None
config = json.load(open("config/config.json"))
current_directory = os.path.abspath(os.path.dirname(__file__))

def encode_font(font_path):
    with open(font_path, "rb") as font_file:
        return base64.b64encode(font_file.read()).decode("utf-8")

font_b64 = encode_font(f"{current_directory}/assets/fonts/ggsans-regular.ttf")
fontmed_base64 = encode_font(f"{current_directory}/assets/fonts/ggsans-medium.ttf")

# ────────────────────────────────────────────────────────────────────────────────
# 🖼️ Génération HTML → Image (BoostPage)
# ────────────────────────────────────────────────────────────────────────────────
class BoostPage:
    def __init__(self, nitro_type, authorname, authoravatar, authortext, receiveravatar, receivername, receivertext):
        self.actual_datetime = datetime.datetime.now()
        self.proof = ""
        self.nitro_type = nitro_type
        self.authorname = authorname
        self.authoravatar = authoravatar
        self.authortext = authortext
        self.sender_message_datetime = (self.actual_datetime - datetime.timedelta(minutes=random.randint(1, 300))).strftime('Today at %I:%M %p')
        self.receivername = receivername
        self.receiveravatar = receiveravatar
        self.receivertext = receivertext
        self.receiver_message_datetime = (self.actual_datetime + datetime.timedelta(minutes=random.randint(1, 120))).strftime('Today at %I:%M %p')

    def get_proof(self):
        nitro_links = {
            "classic": ("https://discord.gift/", f"file://{current_directory}/assets/nitro_presets/nitro_classic_preset.png"),
            "promo": ("https://discord.com/billing/promotions/", f"file://{current_directory}/assets/nitro_presets/nitro_promo_preset.png"),
            "boost": ("https://discord.gift/", f"file://{current_directory}/assets/nitro_presets/nitro_boost_preset.png")
        }
        nitro_link, nitro_image = nitro_links.get(self.nitro_type.lower(), nitro_links["boost"])

        with open(f"{current_directory}/assets/index.html", 'r') as boost_page:
            self.proof = boost_page.read() \
                .replace('GGSANSFONT', f"data:font/ttf;base64,{font_b64}") \
                .replace('GGSANSMEDIUMFONT', f"data:font/ttf;base64,{fontmed_base64}") \
                .replace('AUTHORNAME', self.authorname) \
                .replace('AUTHORAVATAR', self.authoravatar) \
                .replace('AUTHORDATETIME', self.sender_message_datetime) \
                .replace('AUTHORTEXT', self.authortext) \
                .replace('USERNAME', self.receivername) \
                .replace('USERAVATAR', self.receiveravatar) \
                .replace('USERDATETIME', self.receiver_message_datetime) \
                .replace('USERTEXT', self.receivertext) \
                .replace('NITROLINK', nitro_link) \
                .replace('NITROCODE', ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(16))) \
                .replace('NITROIMAGESRC', nitro_image)
        return self.proof

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class FakeNitroProof(commands.Cog):
    """
    Commande /proof et !proof — Génère un faux message Nitro ultra réaliste
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Modal pour receiver custom
    # ────────────────────────────────────────────────────────────────────────────
    class NitroProofCustom(discord.ui.Modal, title='Fake Nitro Proof System'):
        nitrotype = discord.ui.TextInput(label='Type of Nitro code', style=discord.TextStyle.short, placeholder='classic/boost/promo', required=True)
        authortext = discord.ui.TextInput(label='Text sent by you', style=discord.TextStyle.long, required=False)
        receivername = discord.ui.TextInput(label='Receiver Name', style=discord.TextStyle.short, required=True)
        receiveravatar = discord.ui.TextInput(label='Receiver Avatar URL', style=discord.TextStyle.short, required=False)
        receivertext = discord.ui.TextInput(label='Text sent by receiver', style=discord.TextStyle.paragraph, required=True)

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            recv_avatar = self.receiveravatar.value or config["default_avatar"]
            proof_html = BoostPage(
                self.nitrotype.value, 
                interaction.user.display_name, 
                interaction.user.avatar.url, 
                self.authortext.value, 
                recv_avatar, 
                self.receivername.value, 
                self.receivertext.value
            ).get_proof()
            hti.screenshot(html_str=proof_html, size=(random.randint(730, 1100), random.randint(450, 470)), save_as='proof.png')
            await interaction.user.send(file=discord.File('proof.png'))
            await interaction.followup.send("✅ Proof generated! Check your DMs.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Modal pour receiver par ID
    # ────────────────────────────────────────────────────────────────────────────
    class NitroProofId(discord.ui.Modal, title='Fake Nitro Proof System'):
        nitrotype = discord.ui.TextInput(label='Type of Nitro code', style=discord.TextStyle.short, placeholder='classic/boost/promo', required=True)
        authortext = discord.ui.TextInput(label='Text sent by you', style=discord.TextStyle.long, required=False)
        receiverid = discord.ui.TextInput(label='Receiver ID', style=discord.TextStyle.short, required=True)
        receivertext = discord.ui.TextInput(label='Text sent by receiver', style=discord.TextStyle.paragraph, required=True)

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                user = await interaction.client.fetch_user(int(self.receiverid.value))
                author_avatar = interaction.user.display_avatar.url if interaction.user.avatar else config["default_avatar"]
                recv_avatar = user.display_avatar.url if user.avatar else config["default_avatar"]
                proof_html = BoostPage(
                    self.nitrotype.value, 
                    interaction.user.name, 
                    author_avatar, 
                    self.authortext.value, 
                    recv_avatar, 
                    user.name, 
                    self.receivertext.value
                ).get_proof()
                hti.screenshot(html_str=proof_html, size=(random.randint(730, 1100), random.randint(450, 470)), save_as='proof.png')
                await interaction.user.send(file=discord.File('proof.png'))
                await interaction.followup.send("✅ Proof generated! Check your DMs.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande Slash
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="proof", description="Generate a Giveaway Nitro Proof")
    @app_commands.describe(receiverinfo="Choose receiver by ID or custom")
    @app_commands.choices(receiverinfo=[
        app_commands.Choice(name='Receiver ID', value='id'),
        app_commands.Choice(name='Custom Receiver', value='custom')
    ])
    async def slash_proof(self, interaction: discord.Interaction, receiverinfo: str):
        if receiverinfo == 'custom':
            await interaction.response.send_modal(self.NitroProofCustom())
        elif receiverinfo == 'id':
            await interaction.response.send_modal(self.NitroProofId())

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = FakeNitroProof(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Autre"
    await bot.add_cog(cog)
