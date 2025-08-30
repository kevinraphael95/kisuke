# ────────────────────────────────────────────────────────────────────────────────
# 📌 fakenitro_proof.py — Commande interactive /proof et !proof
# Objectif : Générer un faux message Discord Nitro ultra réaliste (HTML→PNG)
# Catégorie : Autre
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput
import datetime, random, os, json, base64
from html2image import Html2Image

from utils.discord_utils import safe_send, safe_respond  

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Configuration
# ────────────────────────────────────────────────────────────────────────────────
hti = Html2Image(custom_flags=["--default-background-color=ffffff"])
hti.browser.use_new_headless = None
current_directory = os.path.abspath(os.path.dirname(__file__))
config = json.load(open("config/config.json"))

def encode_font(font_path):
    with open(font_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

font_b64 = encode_font(f"{current_directory}/assets/fonts/ggsans-regular.ttf")
fontmed_base64 = encode_font(f"{current_directory}/assets/fonts/ggsans-medium.ttf")

# ────────────────────────────────────────────────────────────────────────────────
# 🖼️ Génération HTML → Image
# ────────────────────────────────────────────────────────────────────────────────
class BoostPage:
    def __init__(self, nitro_type, authorname, authoravatar, authortext, receiveravatar, receivername, receivertext):
        self.actual_datetime = datetime.datetime.now()
        self.nitro_type = nitro_type
        self.authorname = authorname
        self.authoravatar = authoravatar
        self.authortext = authortext
        self.sender_message_datetime = (self.actual_datetime - datetime.timedelta(minutes=random.randint(1, 300))).strftime('Today at %I:%M %p')
        self.receivername = receivername
        self.receiveravatar = receiveravatar
        self.receivertext = receivertext
        self.receiver_message_datetime = (self.actual_datetime + datetime.timedelta(minutes=random.randint(1, 120))).strftime('Today at %I:%M %p')
        self.proof = ""

    def get_proof(self):
        nitro_links = {
            "classic": ("https://discord.gift/", f"file://{current_directory}/assets/nitro_presets/nitro_classic_preset.png"),
            "promo": ("https://discord.com/billing/promotions/", f"file://{current_directory}/assets/nitro_presets/nitro_promo_preset.png"),
            "boost": ("https://discord.gift/", f"file://{current_directory}/assets/nitro_presets/nitro_boost_preset.png")
        }
        nitro_link, nitro_image = nitro_links.get(self.nitro_type.lower(), nitro_links["boost"])

        with open(f"{current_directory}/assets/index.html", 'r', encoding="utf-8") as f:
            self.proof = f.read() \
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
    # 🔹 Modal Custom
    # ────────────────────────────────────────────────────────────────────────────
    class NitroProofCustom(Modal, title="Fake Nitro Proof System"):
        nitrotype = TextInput(label="Type of Nitro code", style=discord.TextStyle.short, placeholder="classic/boost/promo", required=True)
        authortext = TextInput(label="Text sent by you", style=discord.TextStyle.long, required=False)
        receivername = TextInput(label="Receiver Name", style=discord.TextStyle.short, required=True)
        receiveravatar = TextInput(label="Receiver Avatar URL", style=discord.TextStyle.short, required=False)
        receivertext = TextInput(label="Text sent by receiver", style=discord.TextStyle.paragraph, required=True)

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            recv_avatar = self.receiveravatar.value or config["default_avatar"]
            author_avatar = interaction.user.display_avatar.url if interaction.user.display_avatar else config["default_avatar"]
            proof_html = BoostPage(
                self.nitrotype.value,
                interaction.user.display_name,
                author_avatar,
                self.authortext.value,
                recv_avatar,
                self.receivername.value,
                self.receivertext.value
            ).get_proof()
            proof_path = os.path.join(current_directory, 'proof.png')
            hti.screenshot(html_str=proof_html, size=(random.randint(730, 1100), random.randint(450, 470)), save_as=proof_path)
            await safe_send(interaction.user, file=discord.File(proof_path))
            await safe_respond(interaction, "✅ Proof generated! Check your DMs.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Modal ID
    # ────────────────────────────────────────────────────────────────────────────
    class NitroProofId(Modal, title="Fake Nitro Proof System"):
        nitrotype = TextInput(label="Type of Nitro code", style=discord.TextStyle.short, placeholder="classic/boost/promo", required=True)
        authortext = TextInput(label="Text sent by you", style=discord.TextStyle.long, required=False)
        receiverid = TextInput(label="Receiver ID", style=discord.TextStyle.short, required=True)
        receivertext = TextInput(label="Text sent by receiver", style=discord.TextStyle.paragraph, required=True)

        async def on_submit(self, interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            try:
                user = await interaction.client.fetch_user(int(self.receiverid.value))
                author_avatar = interaction.user.display_avatar.url if interaction.user.display_avatar else config["default_avatar"]
                recv_avatar = user.display_avatar.url if user.display_avatar else config["default_avatar"]
                proof_html = BoostPage(
                    self.nitrotype.value,
                    interaction.user.display_name,
                    author_avatar,
                    self.authortext.value,
                    recv_avatar,
                    user.display_name,
                    self.receivertext.value
                ).get_proof()
                proof_path = os.path.join(current_directory, 'proof.png')
                hti.screenshot(html_str=proof_html, size=(random.randint(730, 1100), random.randint(450, 470)), save_as=proof_path)
                await safe_send(user, file=discord.File(proof_path))
                await safe_respond(interaction, "✅ Proof generated! Check your DMs.", ephemeral=True)
            except Exception as e:
                await safe_respond(interaction, f"❌ Error: {e}", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="proof",
        description="Generate a Giveaway Nitro Proof"
    )
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_proof(self, interaction: discord.Interaction):
        """Commande slash principale"""
        try:
            view = discord.ui.View(timeout=60)
            # Ajout des boutons pour choisir ID ou Custom
            view.add_item(discord.ui.Button(label="Custom Receiver", style=discord.ButtonStyle.green, custom_id="proof_custom"))
            view.add_item(discord.ui.Button(label="Receiver ID", style=discord.ButtonStyle.blurple, custom_id="proof_id"))
            await safe_respond(interaction, "Choisis le type de receiver :", view=view, ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /proof] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = FakeNitroProof(bot)
    await bot.add_cog(cog)
