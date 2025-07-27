# ────────────────────────────────────────────────────────────────────────────────
# 📌 hollow.py — Commande interactive !hollow
# Objectif : Faire apparaître un Hollow, le joueur peut l’attaquer en dépensant 1 reiatsu
#           et doit accomplir 3 tâches intégrées pour le vaincre.
# Catégorie : Hollow
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View
from discord import Embed
import os
import traceback
from utils.discord_utils import safe_send, safe_edit
from supabase_client import supabase
import asyncio

from utils.taches import get_random_task  # 🧩 Récupérer une tâche aléatoire

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Constantes
# ────────────────────────────────────────────────────────────────────────────────
HOLLOW_IMAGE_PATH = os.path.join("data", "hollows", "hollow0.jpg")
REIATSU_COST = 1

# ──────────────────────────────────────────────────
# 🧠 Vue avec bouton d’attaque
# ──────────────────────────────────────────────────

class HollowView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.attacked = False
        self.message = None

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True
        if self.message:
            try:
                await safe_edit(self.message, view=self)
            except:
                pass

    @discord.ui.button(label=f"Attaquer (1 reiatsu)", style=discord.ButtonStyle.red)
    async def attack(self, inter: discord.Interaction, btn):
        if inter.user.id != self.author_id:
            await inter.response.send_message("❌ Ce bouton n’est pas pour toi.", ephemeral=True)
            return
        if self.attacked:
            await inter.response.send_message("⚠️ Tu as déjà attaqué.", ephemeral=True)
            return

        await inter.response.defer(thinking=True)
        uid = str(inter.user.id)

        try:
            # 🔋 Vérifier le reiatsu
            resp = supabase.table("reiatsu").select("points").eq("user_id", uid).execute()
            if not resp.data or resp.data[0].get("points", 0) < REIATSU_COST:
                await inter.followup.send("❌ Tu n’as pas assez de reiatsu.", ephemeral=True)
                return

            # 🔻 Déduire le reiatsu
            new_points = resp.data[0]["points"] - REIATSU_COST
            supabase.table("reiatsu").update({"points": new_points}).eq("user_id", uid).execute()

            self.attacked = True

            # ⚔️ Modifier l’embed de départ
            embed = self.message.embeds[0]
            embed.description = f"⚔️ {inter.user.display_name} attaque le Hollow !\nRéussis 3 épreuves pour le vaincre."
            embed.clear_fields()
            embed.set_footer(text="Combat en cours...")
            embed.add_field(name="Épreuves", value="⏳ Chargement des épreuves...", inline=False)
            await safe_edit(self.message, embeds=[embed], view=self)

            # 🧪 Lancer les 3 épreuves une à une
            resultat = []
            victoire = True

            for i in range(3):
                nom, fonction = get_random_task()
                success = await fonction(inter, embed=embed, index=i + 1)
                symbole = "✅" if success else "❌"
                resultat.append(f"**Épreuve {i + 1} :** {nom} {symbole}")
                embed.set_field_at(0, name="Épreuves", value="\n".join(resultat), inline=False)
                await safe_edit(self.message, embeds=[embed], view=self)
                await asyncio.sleep(1)
                victoire = victoire and success

            # 🏁 Embed final de résultat
            result_embed = Embed(
                title="🎯 Résultat du combat",
                description="🎉 Tu as vaincu le Hollow !" if victoire else "💀 Tu as échoué à vaincre le Hollow.",
                color=discord.Color.green() if victoire else discord.Color.red()
            )
            result_embed.set_footer(text=f"Combat de {inter.user.display_name}")

            await safe_edit(self.message, embeds=[embed, result_embed], view=self)

        except Exception:
            traceback.print_exc()
            await inter.followup.send("⚠️ Une erreur est survenue pendant le combat.", ephemeral=True)

# ──────────────────────────────────────────────────
# 🧠 Cog principal — HollowCommand
# ──────────────────────────────────────────────────

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
            description=f"Attaque-le pour {REIATSU_COST} reiatsu et réussis 3 tâches.",
            color=discord.Color.dark_red()
        )
        embed.set_image(url="attachment://hollow.jpg")
        embed.set_footer(text="Tu as 60 secondes pour cliquer sur Attaquer.")
        view = HollowView(author_id=ctx.author.id)
        msg = await ctx.send(embed=embed, file=file, view=view)
        view.message = msg


# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HollowCommand(bot)
    for command in cog.get_commands():
        command.category = "Test"
    await bot.add_cog(cog)


