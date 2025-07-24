# ────────────────────────────────────────────────────────────────────────────────
# 📌 hollow.py — Commande interactive !hollow
# Objectif : Faire apparaître un Hollow, le joueur peut l’attaquer en dépensant 50 reiatsu
# Catégorie : Hollow
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import os
import traceback
from utils.discord_utils import safe_send
from supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Constantes
# ────────────────────────────────────────────────────────────────────────────────
HOLLOW_IMAGE_PATH = os.path.join("data", "hollows", "hollow0.jpg")
REIATSU_COST = 50

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Vue avec bouton d’attaque
# ────────────────────────────────────────────────────────────────────────────────
class HollowView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.attacked = False
        self.message = None  # Défini après enregistrement du message par la commande

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass  # Silence si le message n'existe plus

    @discord.ui.button(label=f"Attaquer ({REIATSU_COST} reiatsu)", style=discord.ButtonStyle.red)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Ce bouton n’est pas pour toi.", ephemeral=True)
            return

        if self.attacked:
            await interaction.response.send_message("⚠️ Tu as déjà attaqué ce Hollow.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True)
        user_id = str(interaction.user.id)

        try:
            # Récupération reiatsu
            resp = supabase.table("reiatsu").select("points").eq("user_id", user_id).execute()
            if not resp.data:
                await interaction.followup.send("❌ Tu n’as pas de Reiatsu enregistré.", ephemeral=True)
                return

            points = resp.data[0].get("points", 0)
            if points < REIATSU_COST:
                await interaction.followup.send(f"❌ Il te faut {REIATSU_COST} reiatsu pour attaquer.", ephemeral=True)
                return

            # Mise à jour reiatsu
            new_points = points - REIATSU_COST
            update_resp = supabase.table("reiatsu").update({"points": new_points}).eq("user_id", user_id).execute()
            if not update_resp.data:
                await interaction.followup.send("⚠️ Erreur lors de la mise à jour de ton reiatsu.", ephemeral=True)
                return


            self.attacked = True

            await interaction.followup.send(
                f"🎉 Bravo {interaction.user.display_name}, tu as vaincu le Hollow en dépensant {REIATSU_COST} reiatsu ! Ça sert à rien mais bravo 🤣🤣🤣"
            )

            for child in self.children:
                child.disabled = True

            try:
                # ✅ Correction ici : utiliser self.message au lieu de interaction.message
                await self.message.edit(view=self)
            except discord.NotFound:
                print("[ERREUR EDIT MESSAGE] Le message original n’existe plus (supprimé ?).")
            except discord.Forbidden:
                print("[ERREUR EDIT MESSAGE] Le bot n’a pas les permissions pour modifier ce message.")
            except discord.HTTPException as http_error:
                print(f"[ERREUR EDIT MESSAGE] Erreur HTTP lors de la modification du message : {http_error}")
            except Exception:
                print("[ERREUR EDIT MESSAGE] Erreur inconnue :")
                traceback.print_exc()

        except Exception:
            print("[ERREUR SUPABASE OU INTERACTION] Erreur dans attack_button :")
            traceback.print_exc()
            await interaction.followup.send("⚠️ Une erreur inattendue est survenue.", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal — HollowCommand
# ────────────────────────────────────────────────────────────────────────────────
class HollowCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="hollow",
        help="Fais apparaître un Hollow à attaquer en dépensant 50 reiatsu."
    )
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def hollow(self, ctx: commands.Context):
        if not os.path.isfile(HOLLOW_IMAGE_PATH):
            await safe_send(ctx, "❌ Image du Hollow introuvable.")
            return

        file = discord.File(HOLLOW_IMAGE_PATH, filename="hollow.jpg")
        embed = discord.Embed(
            title="👹 Un Hollow est apparu !",
            description=f"Attaque-le en dépensant {REIATSU_COST} Reiatsu !",
            color=discord.Color.dark_red()
        )
        embed.set_image(url="attachment://hollow.jpg")
        embed.set_footer(text="Tu as 60 secondes pour attaquer.")

        view = HollowView(author_id=ctx.author.id)
        message = await ctx.send(embed=embed, file=file, view=view)
        view.message = message  # ✅ Enregistre bien le message original

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HollowCommand(bot)
    for command in cog.get_commands():
        command.category = "Test"
    await bot.add_cog(cog)
