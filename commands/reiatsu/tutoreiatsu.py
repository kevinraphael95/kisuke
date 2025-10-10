# ────────────────────────────────────────────────────────────────────────────────
# 📌 tutoreiatsu.py — Tutoriel interactif pour nouveaux joueurs
# Objectif : Afficher un guide paginé pour comprendre le système Reiatsu
# Catégorie : Reiatsu
# Accès : Tous
# Cooldown : 1 utilisation / 10s
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button

# ────────────────────────────────────────────────────────────────
# 📌 Pages du tutoriel
# ────────────────────────────────────────────────────────────────
PAGES = [
    {
        "title": "📖 Bienvenue dans le mini-jeu de récolte de Reiatsu",
        "description": (
            "💠 Le Reiatsu apparaît régulièrement sur le serveur (vitesse variable en fonction des paramètres du serveur).\n\n"
            "- Absorbe le Reiatsu en cliquant sur l'emoji sur le message d'apparition du reiatsu.\n"
            "- Le reiatsu normal donne +1, le Super reiatsu rapporte +100 (rare)\n"
            "- Plus tu accumules, plus tu montes dans le classement. Le reiatsu aura des utilités plus tard."
        ),
        "color": discord.Color.purple()
    },
    {
        "title": "⚡ Commandes principales",
        "description": (
            "- `/reiatsu` : Voir les infos générales (salon ou apparaît le Reiatsu et dans combien de temps) et le classement\n"
            "- `/reiatsuprofil` : Voir ton profil, classe, skill et cooldowns"
        ),
        "color": discord.Color.blue()
    },
    {
        "title": "🎭 Choisir une classe",
        "description": (
            "Chaque classe a un **passif** et un **skill actif** :\n\n"
            "🥷 **Voleur** : Réduction cooldown vol de 5h, skill : vol garanti et 15% de chance de doubler le vol (12h)\n"
            "🌀 **Absorbeur** : +5 Reiatsu par absorption, skill : prochain Reiatsu = Super (24h)\n"
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
        "title": "🎟️ KeyLottery",
        "description": (
            "📌 Commande : `/keylottery`\n"
            "- Achète un ticket pour 250 Reiatsu\n"
            "- 10 boutons pour tenter ta chance :\n"
            "🔑 Gagner une clé Steam\n💎 Doubler la mise\n❌ Ne rien gagner"
        ),
        "color": discord.Color.gold()
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

# ────────────────────────────────────────────────────────────────
# 🧠 Vue paginée du tutoriel
# ────────────────────────────────────────────────────────────────
class TutoReiatsuView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.index = 0

    # 🔹 Génération de l'embed actuel
    def get_embed(self):
        page = PAGES[self.index]
        embed = discord.Embed(
            title=page["title"],
            description=page["description"],
            color=page["color"]
        )
        embed.set_footer(text=f"Page {self.index + 1}/{len(PAGES)}")
        return embed

    # 🔹 Vérification utilisateur
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "❌ Tu ne peux pas interagir avec ce tutoriel.", ephemeral=True
            )
            return False
        return True

    # 🔹 Timeout : désactivation des boutons
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if hasattr(self, "message"):
            try:
                await self.message.edit(view=self)
            except:
                pass

    # 🔹 Bouton précédent
    @discord.ui.button(label="⬅️ Précédent", style=discord.ButtonStyle.secondary)
    async def prev_page(self, interaction: discord.Interaction, button: Button):
        self.index = (self.index - 1) % len(PAGES)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    # 🔹 Bouton suivant
    @discord.ui.button(label="➡️ Suivant", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        self.index = (self.index + 1) % len(PAGES)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

# ────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────
class TutoReiatsu(commands.Cog):
    """Commande /tutoreiatsu et !tutoreiatsu — Tutoriel interactif Reiatsu"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🔹 Fonction interne pour envoyer le tutoriel
    async def _send_tuto(self, ctx_or_interaction):
        user_id = ctx_or_interaction.user.id if hasattr(ctx_or_interaction, "user") else ctx_or_interaction.author.id
        view = TutoReiatsuView(user_id)
        embed = view.get_embed()
        if hasattr(ctx_or_interaction, "response"):  # slash
            await ctx_or_interaction.response.send_message(embed=embed, view=view)
            view.message = await ctx_or_interaction.original_message()
        else:
            view.message = await ctx_or_interaction.send(embed=embed, view=view)

    # 🔹 Commande Slash
    @discord.app_commands.command(
        name="tutoreiatsu",
        description="Affiche le tutoriel complet pour les nouveaux joueurs."
    )
    async def slash_tuto(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self._send_tuto(interaction)

    # 🔹 Commande PREFIX
    @commands.command(
        name="tutoreiatsu",
        help="Affiche le tutoriel complet pour les nouveaux joueurs."
    )
    async def prefix_tuto(self, ctx: commands.Context):
        await self._send_tuto(ctx)

# ────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TutoReiatsu(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)


