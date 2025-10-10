# ────────────────────────────────────────────────────────────────────────────────
# 📌 tutoreiatsu.py — Tutoriel interactif /tutoreiatsu et !tutoreiatsu
# Objectif : Afficher un guide interactif paginé pour les nouveaux joueurs
# Catégorie : Reiatsu
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
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Données du tutoriel
# ────────────────────────────────────────────────────────────────────────────────
PAGES = [
    {
        "title": "📖 Bienvenue dans le mini-jeu de Reiatsu",
        "description": (
            "💠 Le Reiatsu apparaît régulièrement sur le serveur sur le salon x.\n\n"
            "- Quand un Reiatsu apparaît sur le serveur, absorbe le en cliquant sur l'emoji en réaction.\n"
            "- Un Reiatsu normal rapporte +1 et un Super Reiatsu rapporte +100 (rare)\n"
            "- Le but est de récupérer le plus de Reiatsu possible, le Reiatsu aura des utilités plus tard."
        ),
        "color": discord.Color.purple()
    },
    {
        "title": "⚡ Commandes principales",
        "description": (
            "- `/reiatsu` : Voir les infos générales et le classement\n"
            "- `/reiatsuprofil` : Voir ton profil, classe, skill et cooldowns"
        ),
        "color": discord.Color.blue()
    },
    {
        "title": "🎭 Choisir une classe",
        "description": (
            "Chaque classe a un **passif** et un **skill actif**\n"
            "Le passif s'active automatiqument, le skill doit être activé.\n\n"
            "🥷 Voleur : Vol garanti possible (12h)\n"
            "🌀 Absorbeur : Prochain Reiatsu = Super (24h)\n"
            "🎭 Illusionniste : Faux Reiatsu, chance de ne rien perdre (8h)\n"
            "🎲 Parieur : Mise pour gagner 30 Reiatsu (12h)"
        ),
        "color": discord.Color.green()
    },
    {
        "title": "🌀 Activer ton skill",
        "description": (
            "📌 Commande : `/skill` ou `!skill`\n\n"
            "- Illusionniste : crée un faux Reiatsu\n"
            "- Voleur : prochain vol garanti\n"
            "- Absorbeur : prochain Reiatsu = Super\n"
            "- Parieur : mise 10 Reiatsu pour tenter d’en gagner 30"
        ),
        "color": discord.Color.orange()
    },
    {
        "title": "🩸 Voler du Reiatsu",
        "description": (
            "📌 Commande : `/reiatsuvol @joueur` ou `!reiatsuvol @joueur`\n\n"
            "- Voler 10% du Reiatsu de la cible\n"
            "- Chances : Voleur 67% / Autres 25%\n"
            "- Skill actif Voleur : vol garanti + double\n"
            "- Illusionniste actif : 50% chance de ne rien perdre\n"
            "- Cooldown : 24h (19h pour Voleur)"
        ),
        "color": discord.Color.red()
    },
    {
        "title": "💡 Conseils pour bien débuter",
        "description": (
            "1. Choisis ta classe selon ton style.\n"
            "2. Active ton skill régulièrement.\n"
            "3. Participe aux vols et aux orbes.\n"
            "4. Consulte ton profil pour points et cooldowns."
        ),
        "color": discord.Color.teal()
    }
]

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Navigation paginée avec boutons
# ────────────────────────────────────────────────────────────────────────────────
class TutoView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.index = 0
        self.message = None

    def get_embed(self):
        page = PAGES[self.index]
        embed = discord.Embed(
            title=page["title"],
            description=page["description"],
            color=page["color"]
        )
        embed.set_footer(text=f"Page {self.index + 1}/{len(PAGES)}")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await safe_edit(interaction.message, content="❌ Tu ne peux pas interagir avec ce tutoriel.", view=None)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            await safe_edit(self.message, view=self)

    @discord.ui.button(label="⬅️ Précédent", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: Button):
        self.index = (self.index - 1) % len(PAGES)
        await safe_edit(interaction.message, embed=self.get_embed(), view=self)

    @discord.ui.button(label="➡️ Suivant", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        self.index = (self.index + 1) % len(PAGES)
        await safe_edit(interaction.message, embed=self.get_embed(), view=self)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class TutoReiatsu(commands.Cog):
    """Commande /tutoreiatsu et !tutoreiatsu — Tutoriel interactif Reiatsu"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🔹 Fonction interne pour envoyer le tutoriel
    async def _send_tuto(self, channel: discord.abc.Messageable, user_id: int):
        view = TutoView(user_id)
        view.message = await safe_send(channel, embed=view.get_embed(), view=view)

    # 🔹 Commande SLASH
    @app_commands.command(
        name="tutoreiatsu",
        description="Affiche le tutoriel complet pour les nouveaux joueurs."
    )
    @app_commands.checks.cooldown(rate=1, per=10.0, key=lambda i: i.user.id)
    async def slash_tuto(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._send_tuto(interaction.channel, interaction.user.id)
        await interaction.delete_original_response()

    # 🔹 Commande PREFIX
    @commands.command(
        name="tutoreiatsu",
        help="Affiche le tutoriel complet pour les nouveaux joueurs."
    )
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_tuto(self, ctx: commands.Context):
        await self._send_tuto(ctx.channel, ctx.author.id)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TutoReiatsu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)


