# ────────────────────────────────────────────────────────────────────────────────
# 📌 tutoreiatsu.py — Tutoriel interactif /tutoreiatsu et !tutoreiatsu
# Objectif : Afficher un guide interactif et paginé avec navigation directe
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
from discord.ui import View, Button, Select
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Données du tutoriel
# ────────────────────────────────────────────────────────────────────────────────
PAGES = [
    {
        "title": "📖 Bienvenue dans Reiatsu",
        "description": (
            "💠 Le Reiatsu est l’énergie principale de ton personnage.\n\n"
            "- Gagné en absorbant des orbes qui apparaissent automatiquement.\n"
            "- Orbes : Normaux (+1) / Super (+100, rare)\n"
            "- Plus tu accumules, plus tu montes dans le classement."
        ),
        "color": discord.Color.purple()
    },
    {
        "title": "⚡ Commandes principales",
        "description": (
            "- `/reiatsu` : Voir le top 10 et infos générales\n"
            "- `/reiatsuprofil` : Voir ton profil, classe, skill et cooldowns"
        ),
        "color": discord.Color.blue()
    },
    {
        "title": "🎭 Choisir une classe",
        "description": (
            "Chaque classe a un **passif** et un **skill actif** :\n\n"
            "🥷 **Voleur** : Réduction cooldown vol, vol garanti possible (12h)\n"
            "🌀 **Absorbeur** : +5 Reiatsu par absorption, prochain Reiatsu = Super (24h)\n"
            "🎭 **Illusionniste** : 50% chance de ne rien perdre si volé, faux Reiatsu (8h)\n"
            "🎲 **Parieur** : Absorption aléatoire, mise pour gagner 30 Reiatsu (12h)"
        ),
        "color": discord.Color.green()
    },
    {
        "title": "🌀 Activer ton skill",
        "description": (
            "📌 Commande : `/skill` ou `!skill`\n\n"
            "- Illusionniste : crée un faux Reiatsu (50 points si pris par un autre)\n"
            "- Voleur : prochain vol garanti\n"
            "- Absorbeur : prochain Reiatsu = Super Reiatsu\n"
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
            "- Cooldown : 24h (19h pour Voleur)\n"
            "- Illusionniste actif : 50% chance de ne rien perdre"
        ),
        "color": discord.Color.red()
    },
    {
        "title": "💡 Conseils pour bien débuter",
        "description": (
            "1. Choisis ta classe selon ton style.\n"
            "2. Active ton skill régulièrement.\n"
            "3. Participe aux vols et aux orbes.\n"
            "4. Consulte ton profil pour points et cooldowns.\n"
            "5. Essaie la KeyLottery pour des récompenses supplémentaires."
        ),
        "color": discord.Color.teal()
    }
]

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Navigation paginée + boutons directs
# ────────────────────────────────────────────────────────────────────────────────
class TutoView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        self.index = 0
        self.message = None
        # Bouton pour navigation directe
        self.add_item(PageSelect(self))

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
            await safe_respond(interaction, "❌ Tu ne peux pas interagir avec ce tutoriel.", ephemeral=True)
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

class PageSelect(Select):
    def __init__(self, parent_view: TutoView):
        self.parent_view = parent_view
        options = [discord.SelectOption(label=f"Page {i+1}", value=str(i)) for i in range(len(PAGES))]
        super().__init__(placeholder="Sauter directement à une page", options=options)

    async def callback(self, interaction: discord.Interaction):
        self.parent_view.index = int(self.values[0])
        await safe_edit(interaction.message, embed=self.parent_view.get_embed(), view=self.parent_view)

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
        name="tutoreiatsu", aliases=["tutorts", "rtstuto", "reiatsututo"],
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


