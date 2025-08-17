# ────────────────────────────────────────────────────────────────────────────────
# 📌 bmoji.py — Commande interactive !bmoji
# Objectif : Deviner quel personnage Bleach se cache derrière un emoji
# Catégorie : Bleach
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
import json, random, os

from utils.discord_utils import safe_send  # pour le préfixe

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des données JSON
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_emojis.json")

def load_characters():
    with open(DATA_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# ⚔️ Fonction commune
# ────────────────────────────────────────────────────────────────────────────────
async def _run_bmoji(target):
    try:
        characters = load_characters()
        if not characters:
            msg = "⚠️ Le fichier d'emojis est vide."
            if isinstance(target, discord.Interaction):
                return await target.response.send_message(msg, ephemeral=True)
            else:
                return await safe_send(target.channel, msg)

        # Tirage du perso
        pers = random.choice(characters)
        nom = pers["nom"]
        emojis = random.sample(pers["emojis"], k=min(3, len(pers["emojis"])))

        # Distracteurs + options
        distracteurs = random.sample([c["nom"] for c in characters if c["nom"] != nom], 3)
        options = distracteurs + [nom]
        random.shuffle(options)

        lettres = ["🇦", "🇧", "🇨", "🇩"]
        bonne = lettres[options.index(nom)]

        # ─────────────── Embed ───────────────
        embed = discord.Embed(
            title="Bmoji",
            description="Devine le personnage de Bleach derrière ces emojis !",
            color=discord.Color.purple()
        )
        embed.add_field(
            name=" ".join(emojis),  # <- Les emojis deviennent le titre, donc plus gros
            value="\n".join(f"{lettres[i]} : {options[i]}" for i in range(4)),
            inline=False
        )


        # ─────────────── Boutons ───────────────
        class PersoButton(discord.ui.Button):
            def __init__(self, emoji, idx):
                super().__init__(emoji=emoji, style=discord.ButtonStyle.secondary)
                self.idx = idx

            async def callback(self, inter_button):
                if isinstance(target, discord.Interaction):
                    if inter_button.user != target.user:
                        return await inter_button.response.send_message("❌ Ce défi ne t'est pas destiné.", ephemeral=True)
                else:
                    if inter_button.user != target.author:
                        return await inter_button.response.send_message("❌ Ce défi ne t'est pas destiné.", ephemeral=True)

                await inter_button.response.defer()
                view.success = (lettres[self.idx] == bonne)
                view.stop()

        view = discord.ui.View(timeout=30)
        for i in range(4):
            view.add_item(PersoButton(lettres[i], i))
        view.success = False

        # ─────────────── Envoi embed ───────────────
        if isinstance(target, discord.Interaction):
            await target.response.send_message(embed=embed, view=view)
            msg = await target.original_response()
        else:
            msg = await safe_send(target.channel, embed=embed, view=view)

        view.message = msg
        await view.wait()

        # ─────────────── Résultat ───────────────
        result_msg = "✅ Bonne réponse" if view.success else f"❌ Mauvaise réponse (c'était {nom})"
        if isinstance(target, discord.Interaction):
            await target.followup.send(result_msg)
        else:
            await safe_send(target.channel, result_msg)

    except FileNotFoundError:
        err = "❌ Fichier `bleach_emojis.json` introuvable."
        if isinstance(target, discord.Interaction):
            await target.response.send_message(err, ephemeral=True)
        else:
            await safe_send(target.channel, err)

    except Exception as e:
        print(f"[ERREUR bmoji] {e}")
        err = "⚠️ Une erreur est survenue."
        if isinstance(target, discord.Interaction):
            await target.response.send_message(err, ephemeral=True)
        else:
            await safe_send(target.channel, err)


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class BMojiCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Préfixe
    @commands.command(name="bmoji", help="Devine quel personnage Bleach se cache derrière ces emojis.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def bmoji_prefix(self, ctx: commands.Context):
        await _run_bmoji(ctx)

    # Slash
    @app_commands.command(name="bmoji", description="Devine quel personnage Bleach se cache derrière ces emojis.")
    async def bmoji_slash(self, interaction: discord.Interaction):
        await _run_bmoji(interaction)


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = BMojiCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Bleach"
    await bot.add_cog(cog)
