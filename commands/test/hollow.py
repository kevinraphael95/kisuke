# ────────────────────────────────────────────────────────────────────────────────
# 📌 hollow.py — Commande interactive !hollow
# Objectif : Lancer un combat contre un Hollow avec 3 épreuves à réussir
# Catégorie : Général
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import random
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Hollow(commands.Cog):
    """
    Commande !hollow — Combat interactif contre un Hollow avec 3 épreuves à réussir.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="hollow",
        help="Lance un combat contre un Hollow avec 3 épreuves à réussir.",
        description="Affiche un embed unique avec 3 mini-jeux à réussir pour vaincre le Hollow."
    )
    async def hollow(self, ctx: commands.Context):
        await ctx.defer()

        # Embed initial
        embed = discord.Embed(
            title="⚔️ Combat contre un Hollow",
            description="Tu dois réussir 3 épreuves pour vaincre le Hollow.",
            color=discord.Color.dark_red()
        )
        embed.set_thumbnail(url="https://i.imgur.com/5e2Z8Iu.png")  # Image Hollow
        embed.add_field(name="Épreuves", value="⚔️ Préparation...", inline=False)

        message = await safe_send(ctx.channel, embed=embed)

        # Fonction d'update de l'embed
        async def update_embed(new_embed):
            try:
                await safe_edit(message, embed=new_embed)
            except discord.HTTPException:
                pass

        # Liste des épreuves disponibles (nom, fonction)
        # Ces fonctions doivent être importées / définies ailleurs,
        # ici ce sont des exemples de noms.
        epreuves = [
            ("Emoji", self.lancer_emoji),
            ("Réflexe", self.lancer_reflexe),
            ("Flèche", self.lancer_fleche),
            ("Infusion", self.lancer_infusion),
            ("Emoji 9", self.lancer_emoji9),
            ("NIM", self.lancer_nim),
        ]

        # Tirage aléatoire de 3 épreuves différentes
        tirage = random.sample(epreuves, 3)

        # Initialise la valeur du champ "Épreuves"
        embed.set_field_at(0, name="Épreuves", value="", inline=False)
        await update_embed(embed)

        succes_total = []

        # Boucle sur les 3 épreuves
        for i, (nom, func) in enumerate(tirage, start=1):
            # Mise à jour texte dans le champ
            nouvelle_valeur = embed.fields[0].value + f"**Épreuve {i} — {nom}**\n"
            embed.set_field_at(0, name="Épreuves", value=nouvelle_valeur, inline=False)
            await update_embed(embed)

            # Lance l'épreuve
            succes = await func(ctx, embed, update_embed, i)
            succes_total.append(succes)

            # Ajoute le résultat de l'épreuve dans le champ
            resultat = "✅ Réussie !" if succes else "❌ Échec"
            nouvelle_valeur += f"→ {resultat}\n\n"
            embed.set_field_at(0, name="Épreuves", value=nouvelle_valeur, inline=False)
            await update_embed(embed)

        # Résultat final
        if all(succes_total):
            embed.description = "🎉 Tu as vaincu le Hollow !"
            embed.color = discord.Color.green()
        else:
            embed.description = "💀 Le Hollow t’a vaincu..."
            embed.color = discord.Color.red()

        await update_embed(embed)

    # ────────────────────────────────────────────────────────────────────────────────
    # Exemple de mini-jeux (placeholders, à remplacer par tes vraies fonctions)
    # Chaque fonction doit retourner True (réussite) ou False (échec).
    # Elles doivent recevoir (ctx, embed, update_embed, numéro_de_l_epreuve)
    # ────────────────────────────────────────────────────────────────────────────────

    async def lancer_emoji(self, ctx, embed, update_embed, num):
        # Exemple simple : simuler un mini-jeu qui réussit aléatoirement
        await safe_send(ctx.channel, "Mini-jeu Emoji démarré...")
        # ... ton code ici ...
        return random.choice([True, False])

    async def lancer_reflexe(self, ctx, embed, update_embed, num):
        await safe_send(ctx.channel, "Mini-jeu Réflexe démarré...")
        return random.choice([True, False])

    async def lancer_fleche(self, ctx, embed, update_embed, num):
        await safe_send(ctx.channel, "Mini-jeu Flèche démarré...")
        return random.choice([True, False])

    async def lancer_infusion(self, ctx, embed, update_embed, num):
        await safe_send(ctx.channel, "Mini-jeu Infusion démarré...")
        return random.choice([True, False])

    async def lancer_emoji9(self, ctx, embed, update_embed, num):
        await safe_send(ctx.channel, "Mini-jeu Emoji9 démarré...")
        return random.choice([True, False])

    async def lancer_nim(self, ctx, embed, update_embed, num):
        await safe_send(ctx.channel, "Mini-jeu NIM démarré...")
        return random.choice([True, False])

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Hollow(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Test"
    await bot.add_cog(cog)
