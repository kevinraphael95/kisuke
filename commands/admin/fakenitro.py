# ────────────────────────────────────────────────────────────────────────────────
# 📌 fakenitro_admin.py — Commande interactive /fakenitro et !fakenitro
# Objectif : Simuler un Nitro ultra réaliste et choisir le gagnant par ID
# Catégorie : Autre
# Accès : Admin uniquement
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random
import string

from utils.discord_utils import safe_send, safe_respond  

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class FakeNitroAdmin(commands.Cog):
    """
    Commande /fakenitro et !fakenitro — Simule un Nitro ultra réaliste et permet de choisir le gagnant
    """
    NITRO_LOGO_URL = "https://cdn.discordapp.com/attachments/1070/1070/nitro_logo.png"
    NITRO_EMOJI = "nitrowumpus"

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Génération d'un compte Nitro
    # ────────────────────────────────────────────────────────────────────────────
    def generate_nitro_account(self, user: discord.Member):
        # On prend le pseudo du membre choisi pour plus de réalisme
        username = user.name
        discriminator = user.discriminator
        nitro_type = random.choice(["Nitro Classic", "Nitro Boost"])
        expires_in = f"{random.randint(1, 30)} jours restants"
        return {
            "Pseudo": f"{username}#{discriminator}",
            "Type Nitro": nitro_type,
            "Expiration": expires_in,
            "Lien": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll
        }

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Création de l'embed ultra réaliste
    # ────────────────────────────────────────────────────────────────────────────
    def create_nitro_embed(self, account: dict):
        embed = discord.Embed(
            title=f"🎉 {self.NITRO_EMOJI} Vous avez reçu un Nitro !",
            description="Merci d’utiliser Discord ! Réclame ton Nitro ci-dessous.",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=self.NITRO_LOGO_URL)
        for key, value in account.items():
            if key != "Lien":
                embed.add_field(name=key, value=value, inline=False)
        embed.set_footer(text="Discord • Nitro Gratuit", icon_url=self.NITRO_LOGO_URL)
        return embed

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Vérifie si l'utilisateur est admin
    # ────────────────────────────────────────────────────────────────────────────
    def is_admin():
        async def predicate(interaction: discord.Interaction):
            return interaction.user.guild_permissions.administrator
        return app_commands.check(predicate)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="fakenitro",
        description="Simule un Nitro ultra réaliste pour un membre spécifique !"
    )
    @is_admin()
    async def slash_fakenitro(self, interaction: discord.Interaction, member: discord.Member):
        """Commande slash pour envoyer un faux Nitro à un membre précis"""
        try:
            await interaction.response.defer()
            account = self.generate_nitro_account(member)
            embed = self.create_nitro_embed(account)

            view = View()
            button = Button(
                label="Réclamer mon Nitro",
                url=account["Lien"],
                style=discord.ButtonStyle.link
            )
            view.add_item(button)

            await safe_send(interaction.channel, embed=embed, view=view)
            await interaction.delete_original_response()
        except Exception as e:
            print(f"[ERREUR /fakenitro] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="fakenitro")
    @commands.has_permissions(administrator=True)
    async def prefix_fakenitro(self, ctx: commands.Context, member: discord.Member):
        """Commande préfixe pour envoyer un faux Nitro à un membre précis"""
        try:
            account = self.generate_nitro_account(member)
            embed = self.create_nitro_embed(account)

            view = View()
            button = Button(
                label="Réclamer mon Nitro",
                url=account["Lien"],
                style=discord.ButtonStyle.link
            )
            view.add_item(button)

            await safe_send(ctx.channel, embed=embed, view=view)
        except commands.MissingPermissions:
            await safe_send(ctx.channel, "❌ Vous devez être administrateur pour utiliser cette commande.")
        except Exception as e:
            print(f"[ERREUR !fakenitro] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = FakeNitroAdmin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Admin"
    await bot.add_cog(cog)
