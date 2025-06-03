# ────────────────────────────────────────────────────────────────────────────────
# 📌 gay.py — Commande interactive !gay
# Objectif : Calcule un taux de gaytitude fixe et fun pour un utilisateur Discord
# Catégorie : 🌈 Fun
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import hashlib
import random

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class GayCommand(commands.Cog):
    """
    Commande !gay — Calcule un taux de gaytitude fixe et fun pour un utilisateur Discord
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="gay",
        help="🌈 Calcule ton taux de gaytitude fixe et fun."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def gay(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        # 🔒 Score fixe basé sur le hash de l’ID utilisateur
        user_id = str(member.id).encode()
        hash_val = hashlib.md5(user_id).digest()
        score = int.from_bytes(hash_val, 'big') % 101

        # 📊 Barre de progression visuelle
        filled = "█" * (score // 10)
        empty = "░" * (10 - (score // 10))
        bar = f"`{filled}{empty}`"

        # 📚 Définition des niveaux
        niveaux = [
            {
                "min": 90,
                "emoji": "🌈",
                "titre": "Légende arc-en-ciel",
                "couleur": discord.Color.magenta(),
                "descriptions": [
                    "Ton aura pourrait repeindre une Pride entière.",
                    "Tu transformes chaque salle en comédie musicale.",
                    "Ta playlist est légalement un drapeau."
                ]
            },
            {
                "min": 70,
                "emoji": "💖",
                "titre": "Icône de style",
                "couleur": discord.Color.pink(),
                "descriptions": [
                    "Tu portes plus de motifs que Zara.",
                    "Tu brilles sans filtre.",
                    "Ton regard déclenche des coming-outs."
                ]
            },
            {
                "min": 50,
                "emoji": "🌀",
                "titre": "Curieux·se affirmé·e",
                "couleur": discord.Color.blurple(),
                "descriptions": [
                    "Tu es une énigme en glitter.",
                    "Explorateur.rice de toutes les vibes.",
                    "Ton cœur a plus de bissections qu’un shōnen."
                ]
            },
            {
                "min": 30,
                "emoji": "🤔",
                "titre": "Questionnement doux",
                "couleur": discord.Color.gold(),
                "descriptions": [
                    "Tu dis ‘non’ mais ton historique dit ‘peut-être’.",
                    "Un mojito et tout peut basculer.",
                    "T’as déjà dit ‘je suis fluide, genre dans l’humour’."
                ]
            },
            {
                "min": 0,
                "emoji": "📏",
                "titre": "Straight mode activé",
                "couleur": discord.Color.dark_gray(),
                "descriptions": [
                    "Tu joues à FIFA et ça te suffit.",
                    "Ton placard contient 50 tee-shirts gris.",
                    "Même ton Wi-Fi est en ligne droite."
                ]
            }
        ]

        # 🎯 Sélection du bon niveau et commentaire
        niveau = next(n for n in niveaux if score >= n["min"])
        commentaire = random.choice(niveau["descriptions"])

        # 🖼️ Création de l'embed
        embed = discord.Embed(
            title=f"{niveau['emoji']} {niveau['titre']}",
            description=commentaire,
            color=niveau["couleur"]
        )
        embed.set_author(
            name=f"Taux de gaytitude de {member.display_name}",
            icon_url=member.avatar.url if member.avatar else None
        )
        embed.add_field(name="📊 Pourcentage", value=f"**{score}%**", inline=True)
        embed.add_field(name="📈 Niveau", value=bar, inline=False)
        embed.set_footer(text="✨ C’est scientifique. Enfin presque.")

        # 📤 Envoi de l'embed dans le salon
        await ctx.send(embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot):
    cog = GayCommand(bot)
    for command in cog.get_commands():
        command.category = "Fun"  # 📁 Classement dans la catégorie "Fun"
    await bot.add_cog(cog)
