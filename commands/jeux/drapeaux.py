# ────────────────────────────────────────────────────────────────────────────────
# 📌 drapeaux.py — Commande interactive /drapeaux et !drapeaux
# Objectif : Deviner le pays à partir d'un drapeau aléatoire (tous les pays)
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random

# Utils sécurisés
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Liste complète des pays et codes ISO
# ────────────────────────────────────────────────────────────────────────────────
COUNTRIES = {
    "Afghanistan": "af", "Afrique du Sud": "za", "Albanie": "al", "Algérie": "dz",
    "Allemagne": "de", "Andorre": "ad", "Angola": "ao", "Antigua-et-Barbuda": "ag",
    "Arabie saoudite": "sa", "Argentine": "ar", "Arménie": "am", "Australie": "au",
    "Autriche": "at", "Azerbaïdjan": "az", "Bahamas": "bs", "Bahreïn": "bh",
    "Bangladesh": "bd", "Barbade": "bb", "Belgique": "be", "Belize": "bz",
    "Bénin": "bj", "Bhoutan": "bt", "Biélorussie": "by", "Birmanie": "mm",
    "Bolivie": "bo", "Bosnie-Herzégovine": "ba", "Botswana": "bw", "Brésil": "br",
    "Brunei": "bn", "Bulgarie": "bg", "Burkina Faso": "bf", "Burundi": "bi",
    "Cambodge": "kh", "Cameroun": "cm", "Canada": "ca", "Cap-Vert": "cv",
    "Chili": "cl", "Chine": "cn", "Chypre": "cy", "Colombie": "co",
    "Comores": "km", "Congo": "cg", "Corée du Nord": "kp", "Corée du Sud": "kr",
    "Costa Rica": "cr", "Croatie": "hr", "Cuba": "cu", "Danemark": "dk",
    "Djibouti": "dj", "Dominique": "dm", "Égypte": "eg", "Émirats arabes unis": "ae",
    "Équateur": "ec", "Érythrée": "er", "Espagne": "es", "Estonie": "ee",
    "Eswatini": "sz", "États-Unis": "us", "Éthiopie": "et", "Fidji": "fj",
    "Finlande": "fi", "France": "fr", "Gabon": "ga", "Gambie": "gm",
    "Géorgie": "ge", "Ghana": "gh", "Grèce": "gr", "Grenade": "gd",
    "Guatemala": "gt", "Guinée": "gn", "Guinée-Bissau": "gw", "Guinée équatoriale": "gq",
    "Guyana": "gy", "Haïti": "ht", "Honduras": "hn", "Hongrie": "hu",
    "Îles Marshall": "mh", "Îles Salomon": "sb", "Inde": "in", "Indonésie": "id",
    "Iran": "ir", "Irak": "iq", "Irlande": "ie", "Islande": "is",
    "Israël": "il", "Italie": "it", "Jamaïque": "jm", "Japon": "jp",
    "Jordanie": "jo", "Kazakhstan": "kz", "Kenya": "ke", "Kirghizistan": "kg",
    "Kiribati": "ki", "Koweït": "kw", "Laos": "la", "Lesotho": "ls",
    "Lettonie": "lv", "Liban": "lb", "Liberia": "lr", "Libye": "ly",
    "Liechtenstein": "li", "Lituanie": "lt", "Luxembourg": "lu", "Madagascar": "mg",
    "Malaisie": "my", "Malawi": "mw", "Maldives": "mv", "Mali": "ml",
    "Malte": "mt", "Maroc": "ma", "Maurice": "mu", "Mauritanie": "mr",
    "Mexique": "mx", "Micronésie": "fm", "Moldavie": "md", "Monaco": "mc",
    "Mongolie": "mn", "Monténégro": "me", "Mozambique": "mz", "Namibie": "na",
    "Nauru": "nr", "Népal": "np", "Nicaragua": "ni", "Niger": "ne",
    "Nigéria": "ng", "Norvège": "no", "Nouvelle-Zélande": "nz", "Oman": "om",
    "Ouganda": "ug", "Ouzbékistan": "uz", "Pakistan": "pk", "Palaos": "pw",
    "Panama": "pa", "Papouasie-Nouvelle-Guinée": "pg", "Paraguay": "py", "Pays-Bas": "nl",
    "Pérou": "pe", "Philippines": "ph", "Pologne": "pl", "Portugal": "pt",
    "Qatar": "qa", "République centrafricaine": "cf", "République dominicaine": "do",
    "République tchèque": "cz", "Roumanie": "ro", "Royaume-Uni": "gb", "Russie": "ru",
    "Rwanda": "rw", "Saint-Christophe-et-Niévès": "kn", "Sainte-Lucie": "lc",
    "Saint-Marin": "sm", "Saint-Vincent-et-les-Grenadines": "vc", "Salvador": "sv",
    "Samoa": "ws", "Sao Tomé-et-Principe": "st", "Sénégal": "sn", "Serbie": "rs",
    "Seychelles": "sc", "Sierra Leone": "sl", "Singapour": "sg", "Slovaquie": "sk",
    "Slovénie": "si", "Somalie": "so", "Soudan": "sd", "Soudan du Sud": "ss",
    "Sri Lanka": "lk", "Suède": "se", "Suisse": "ch", "Syrie": "sy",
    "Taïwan": "tw", "Tadjikistan": "tj", "Tanzanie": "tz", "Thaïlande": "th",
    "Timor oriental": "tl", "Togo": "tg", "Tonga": "to", "Trinité-et-Tobago": "tt",
    "Tunisie": "tn", "Turkménistan": "tm", "Turquie": "tr", "Tuvalu": "tv",
    "Ukraine": "ua", "Uruguay": "uy", "Vanuatu": "vu", "Vatican": "va",
    "Venezuela": "ve", "Viêt Nam": "vn", "Yémen": "ye", "Zambie": "zm",
    "Zimbabwe": "zw"
}


def get_flag_url(iso_code: str) -> str:
    return f"https://flagcdn.com/w320/{iso_code}.png"

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue interactive — boutons pour choix multiple
# ────────────────────────────────────────────────────────────────────────────────
class FlagQuizView(View):
    def __init__(self, country: str, options: list[str], user: discord.User):
        super().__init__(timeout=30)
        self.country = country
        self.user = user
        self.options = options
        self.buttons = []
        for option in options:
            btn = Button(label=option, style=discord.ButtonStyle.primary)
            btn.callback = self.make_callback(option)
            self.add_item(btn)
            self.buttons.append(btn)

    def make_callback(self, option: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user.id:
                return await interaction.response.send_message(
                    "❌ Ce quiz n'est pas pour toi !", ephemeral=True
                )
            for btn in self.buttons:
                btn.disabled = True
                if btn.label == self.country:
                    btn.style = discord.ButtonStyle.success
                elif btn.label == option:
                    btn.style = discord.ButtonStyle.danger
            await interaction.response.edit_message(view=self)
        return callback

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Drapeaux(commands.Cog):
    """Commande /drapeaux et !drapeaux — Deviner le pays à partir d'un drapeau"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _send_quiz(self, channel: discord.abc.Messageable, user: discord.User):
        country, iso_code = random.choice(list(COUNTRIES.items()))
        flag_url = get_flag_url(iso_code)
        wrong_options = random.sample([c for c in COUNTRIES.keys() if c != country], 3)
        options = wrong_options + [country]
        random.shuffle(options)

        view = FlagQuizView(country, options, user)
        embed = discord.Embed(
            title="🌍 Devine le pays !",
            description="Quel pays correspond à ce drapeau ?",
            color=discord.Color.blurple()
        )
        embed.set_image(url=flag_url)
        await safe_send(channel, embed=embed, view=view)

    # ────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="drapeaux",
        description="Devine le pays à partir d'un drapeau"
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: i.user.id)
    async def slash_drapeaux(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await self._send_quiz(interaction.channel, interaction.user)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /drapeaux] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────
    @commands.command(name="drapeaux")
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_drapeaux(self, ctx: commands.Context):
        try:
            await self._send_quiz(ctx.channel, ctx.author)
        except Exception as e:
            print(f"[ERREUR !drapeaux] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Drapeaux(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
