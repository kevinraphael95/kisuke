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
    "Afghanistan": "af", "Albania": "al", "Algeria": "dz", "Andorra": "ad",
    "Angola": "ao", "Antigua and Barbuda": "ag", "Argentina": "ar", "Armenia": "am",
    "Australia": "au", "Austria": "at", "Azerbaijan": "az", "Bahamas": "bs",
    "Bahrain": "bh", "Bangladesh": "bd", "Barbados": "bb", "Belarus": "by",
    "Belgium": "be", "Belize": "bz", "Benin": "bj", "Bhutan": "bt",
    "Bolivia": "bo", "Bosnia and Herzegovina": "ba", "Botswana": "bw", "Brazil": "br",
    "Brunei": "bn", "Bulgaria": "bg", "Burkina Faso": "bf", "Burundi": "bi",
    "Cambodia": "kh", "Cameroon": "cm", "Canada": "ca", "Cape Verde": "cv",
    "Central African Republic": "cf", "Chad": "td", "Chile": "cl", "China": "cn",
    "Colombia": "co", "Comoros": "km", "Congo": "cg", "Costa Rica": "cr",
    "Croatia": "hr", "Cuba": "cu", "Cyprus": "cy", "Czech Republic": "cz",
    "Denmark": "dk", "Djibouti": "dj", "Dominica": "dm", "Dominican Republic": "do",
    "Ecuador": "ec", "Egypt": "eg", "El Salvador": "sv", "Equatorial Guinea": "gq",
    "Eritrea": "er", "Estonia": "ee", "Eswatini": "sz", "Ethiopia": "et",
    "Fiji": "fj", "Finland": "fi", "France": "fr", "Gabon": "ga",
    "Gambia": "gm", "Georgia": "ge", "Germany": "de", "Ghana": "gh",
    "Greece": "gr", "Grenada": "gd", "Guatemala": "gt", "Guinea": "gn",
    "Guinea-Bissau": "gw", "Guyana": "gy", "Haiti": "ht", "Honduras": "hn",
    "Hungary": "hu", "Iceland": "is", "India": "in", "Indonesia": "id",
    "Iran": "ir", "Iraq": "iq", "Ireland": "ie", "Israel": "il",
    "Italy": "it", "Jamaica": "jm", "Japan": "jp", "Jordan": "jo",
    "Kazakhstan": "kz", "Kenya": "ke", "Kiribati": "ki", "North Korea": "kp",
    "South Korea": "kr", "Kuwait": "kw", "Kyrgyzstan": "kg", "Laos": "la",
    "Latvia": "lv", "Lebanon": "lb", "Lesotho": "ls", "Liberia": "lr",
    "Libya": "ly", "Liechtenstein": "li", "Lithuania": "lt", "Luxembourg": "lu",
    "Madagascar": "mg", "Malawi": "mw", "Malaysia": "my", "Maldives": "mv",
    "Mali": "ml", "Malta": "mt", "Marshall Islands": "mh", "Mauritania": "mr",
    "Mauritius": "mu", "Mexico": "mx", "Micronesia": "fm", "Moldova": "md",
    "Monaco": "mc", "Mongolia": "mn", "Montenegro": "me", "Morocco": "ma",
    "Mozambique": "mz", "Myanmar": "mm", "Namibia": "na", "Nauru": "nr",
    "Nepal": "np", "Netherlands": "nl", "New Zealand": "nz", "Nicaragua": "ni",
    "Niger": "ne", "Nigeria": "ng", "North Macedonia": "mk", "Norway": "no",
    "Oman": "om", "Pakistan": "pk", "Palau": "pw", "Panama": "pa",
    "Papua New Guinea": "pg", "Paraguay": "py", "Peru": "pe", "Philippines": "ph",
    "Poland": "pl", "Portugal": "pt", "Qatar": "qa", "Romania": "ro",
    "Russia": "ru", "Rwanda": "rw", "Saint Kitts and Nevis": "kn", "Saint Lucia": "lc",
    "Saint Vincent and the Grenadines": "vc", "Samoa": "ws", "San Marino": "sm",
    "Sao Tome and Principe": "st", "Saudi Arabia": "sa", "Senegal": "sn",
    "Serbia": "rs", "Seychelles": "sc", "Sierra Leone": "sl", "Singapore": "sg",
    "Slovakia": "sk", "Slovenia": "si", "Solomon Islands": "sb", "Somalia": "so",
    "South Africa": "za", "South Sudan": "ss", "Spain": "es", "Sri Lanka": "lk",
    "Sudan": "sd", "Suriname": "sr", "Sweden": "se", "Switzerland": "ch",
    "Syria": "sy", "Taiwan": "tw", "Tajikistan": "tj", "Tanzania": "tz",
    "Thailand": "th", "Togo": "tg", "Tonga": "to", "Trinidad and Tobago": "tt",
    "Tunisia": "tn", "Turkey": "tr", "Turkmenistan": "tm", "Tuvalu": "tv",
    "Uganda": "ug", "Ukraine": "ua", "United Arab Emirates": "ae",
    "United Kingdom": "gb", "United States": "us", "Uruguay": "uy",
    "Uzbekistan": "uz", "Vanuatu": "vu", "Vatican City": "va", "Venezuela": "ve",
    "Vietnam": "vn", "Yemen": "ye", "Zambia": "zm", "Zimbabwe": "zw"
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
