# ───────────────────────────────────────────────────────────────────────
# 📌 kido_command.py — Commande interactive !kido
# Objectif : Lancer un sort de Kidō avec animation et incantation
# Catégorie : Bleach
# Accès : Public
# ──────────────────────────────────────────────────────────────────

# ───────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ───────────────────────────────────────────────────
import discord
from discord.ext import commands
import json
import asyncio
import os

# ───────────────────────────────────────────────────
# 📂 Chargement des données Kidō
# ───────────────────────────────────────────────────
KIDO_FILE = os.path.join("data", "kido.json")

def load_kido_data():
    with open(KIDO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# ───────────────────────────────────────────────────
# 🧠 Cog principal
# ───────────────────────────────────────────────────
class Kido(commands.Cog):
    """
    Commande !kido — Lance un sort de Kidō avec animation et incantation.
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="kido",
        help="🎼 Lance un sort de Kidō ! Syntaxe : `!!kido <type> <numéro>`",
        description="Exemple : `!!kido bakudo 61`"
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🧊 Anti-spam : 3 secondes
    async def kido(self, ctx, type_kido: str.lower, numero: int):
        try:
            data = load_kido_data()
            type_kido = type_kido.lower()

            if type_kido not in data:
                await ctx.send(f"❌ Type de Kidō inconnu : `{type_kido}`.")
                return

            sort = next((k for k in data[type_kido] if k["numero"] == numero), None)
            if not sort:
                await ctx.send(f"❌ Aucun sort {type_kido} numéro {numero} trouvé.")
                return

            nom = sort["nom"]
            incantation = sort.get("incantation")
            image = sort.get("image")

            # ⏳ Animation dramatique
            loading = await ctx.send(f"🤘 Concentration... (`{type_kido.title()} #{numero}`)")
            await asyncio.sleep(1.5)

            # 📈 Embed final
            embed = discord.Embed(
                title=f"{type_kido.title()} #{numero} — {nom}",
                color=discord.Color.purple()
            )
            embed.add_field(name="🎼 Sort lancé par", value=ctx.author.mention, inline=False)
            embed.add_field(name="📜 Incantation", value=f"*{incantation}*" if incantation else "*(Aucune incantation connue)*", inline=False)
            if image:
                embed.set_image(url=image)

            await loading.edit(content=None, embed=embed)

        except FileNotFoundError:
            await ctx.send("❌ Le fichier `kido.json` est introuvable.")
        except Exception as e:
            await ctx.send(f"⚠️ Erreur : `{e}`")

# ───────────────────────────────────────────────────
# 🔌 Setup du Cog
# ───────────────────────────────────────────────────
async def setup(bot):
    cog = Kido(bot)
    for command in cog.get_commands():
        command.category = "Bleach"
    await bot
                   .add_cog(cog)
