# ────────────────────────────────────────────────────────────────────────────────
# 📌 hollow.py — Commande interactive !hollow
# Objectif : Faire apparaître un Hollow, attaquer (1 reiatsu), réussir 3 tâches.
# Catégorie : Hollow
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# 📦 Imports
import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import Embed
import os
import traceback
from utils.discord_utils import safe_send, safe_edit
from supabase_client import supabase
from utils.taches import TACHES_DISPONIBLES
import asyncio
import random

# 📂 Constantes
HOLLOW_IMAGE_PATH = os.path.join("data", "hollows", "hollow0.jpg")
REIATSU_COST = 1

# 🧪 Lancer les 3 tâches dans un seul embed (champ "Tâche en cours" dynamique)
async def lancer_3_taches_dans_embed(interaction: discord.Interaction, embed: discord.Embed, message: discord.Message) -> bool:
    taches = random.sample(TACHES_DISPONIBLES, 3)
    for idx, tache in enumerate(taches, 1):
        embed.set_field_at(
            1,
            name="Tâche en cours",
            value=f"🧪 Épreuve {idx}/3 en cours...",
            inline=False
        )
        await safe_edit(message, embed=embed)
        await asyncio.sleep(1)
        reussi = await tache(interaction)
        if not reussi:
            embed.set_field_at(1, name="Tâche en cours", value="❌ Tu as échoué. Le Hollow s’enfuit !", inline=False)
            await safe_edit(message, embed=embed)
            return False
    embed.set_field_at(1, name="Tâche en cours", value="🎉 Tu as vaincu le Hollow !", inline=False)
    await safe_edit(message, embed=embed)
    return True

# 🎮 Vue avec bouton d’attaque
class HollowView(View):
    def __init__(self, author_id: int, embed: discord.Embed):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.attacked = False
        self.message = None
        self.embed = embed

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True
        if self.message:
            try:
                await safe_edit(self.message, view=self)
            except:
                pass

    @discord.ui.button(label="⚔️ Attaquer (1 reiatsu)", style=discord.ButtonStyle.danger)
    async def attack(self, inter: discord.Interaction, btn: Button):
        if inter.user.id != self.author_id:
            await inter.response.send_message("❌ Ce bouton ne t'est pas destiné.", ephemeral=True)
            return
        if self.attacked:
            await inter.response.send_message("⚠️ Tu as déjà attaqué.", ephemeral=True)
            return

        await inter.response.defer(thinking=True)
        uid = str(inter.user.id)

        try:
            # 🔋 Vérification du reiatsu
            resp = supabase.table("reiatsu").select("points").eq("user_id", uid).execute()
            points = resp.data[0]["points"] if resp.data else 0

            if points < REIATSU_COST:
                await inter.followup.send("❌ Tu n'as pas assez de reiatsu.", ephemeral=True)
                return

            # 🔻 Déduction
            supabase.table("reiatsu").update({"points": points - REIATSU_COST}).eq("user_id", uid).execute()
            self.attacked = True

            # 🎯 Mise à jour de l’embed avec les champs de combat
            self.embed.description = f"⚔️ {inter.user.display_name} dépense 1 reiatsu pour affronter le Hollow !\n\nRéussis les 3 épreuves pour le vaincre."
            self.embed.set_footer(text="Combat en cours...")
            self.embed.set_field_at(0, name="Épreuves", value="Tu devras réussir 3 tâches aléatoires. Bonne chance !", inline=False)
            self.embed.add_field(name="Tâche en cours", value="⏳ Préparation de l’épreuve...", inline=False)
            await safe_edit(self.message, embed=self.embed, view=self)

            # 🧪 Lancement des épreuves
            victoire = await lancer_3_taches_dans_embed(inter, self.embed, self.message)

            # 🔒 Désactiver le bouton
            for c in self.children:
                c.disabled = True
            await safe_edit(self.message, view=self)

        except Exception:
            traceback.print_exc()
            await inter.followup.send("⚠️ Une erreur est survenue pendant le combat.", ephemeral=True)

# 🧠 Cog principal
class HollowCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="hollow", help="Fais apparaître un Hollow à attaquer")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def hollow(self, ctx: commands.Context):
        if not os.path.isfile(HOLLOW_IMAGE_PATH):
            await safe_send(ctx, "❌ Image du Hollow introuvable.")
            return

        file = discord.File(HOLLOW_IMAGE_PATH, filename="hollow.jpg")
        embed = Embed(
            title="👹 Un Hollow est apparu !",
            description=f"Appuie sur **Attaquer** pour dépenser {REIATSU_COST} reiatsu et tenter de le vaincre.",
            color=discord.Color.dark_red()
        )
        embed.set_image(url="attachment://hollow.jpg")
        embed.set_footer(text="Tu as 60 secondes pour cliquer sur Attaquer.")
        embed.add_field(name="Épreuves", value="Appuie sur le bouton pour commencer.", inline=False)

        view = HollowView(author_id=ctx.author.id, embed=embed)
        msg = await ctx.send(embed=embed, file=file, view=view)
        view.message = msg

# 🔌 Setup du Cog
async def setup(bot: commands.Bot):
    cog = HollowCommand(bot)
    for command in cog.get_commands():
        command.category = "Hollow"
    await bot.add_cog(cog)
