# ──────────────────────────────────────────────────────────────
# 📁 HOLLOW — Lancer une tâche spéciale (infusion Reiatsu)
# ──────────────────────────────────────────────────────────────

# 📦 IMPORTS
import discord
from discord.ext import commands
from supabase_client import supabase
from tasks.test_taches import lancer_infusion  # ⬅️ Tu as déjà cette fonction

# 🎮 UI — Vue avec bouton “Payer le prix”
class HollowView(discord.ui.View):
    def __init__(self, ctx, prix: int):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.prix = prix

    @discord.ui.button(label="💠 Payer le prix en Reiatsu", style=discord.ButtonStyle.primary)
    async def payer_reiatsu(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ Ce bouton ne t’est pas destiné.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        username = interaction.user.display_name

        try:
            # 📡 Récupérer les points actuels depuis Supabase
            data = supabase.table("reiatsu").select("points").eq("user_id", user_id).execute()
            current_points = data.data[0]["points"] if data.data else 0

            if current_points < self.prix:
                await interaction.response.send_message(
                    f"❌ Tu n’as pas assez de Reiatsu ! Il te faut **{self.prix}** points.",
                    ephemeral=True
                )
                return

            # 🔄 Mise à jour : retrait des points
            new_points = current_points - self.prix
            if data.data:
                supabase.table("reiatsu").update({
                    "points": new_points
                }).eq("user_id", user_id).execute()
            else:
                supabase.table("reiatsu").insert({
                    "user_id": user_id,
                    "username": username,
                    "points": new_points
                }).execute()

            # ✅ Confirmation et lancement de la tâche
            await interaction.response.edit_message(
                content="💠 Tu as payé le prix. Une sensation spirituelle t’envahit...",
                view=None
            )
            await lancer_infusion(interaction)

        except Exception as e:
            await interaction.response.send_message(
                f"⚠️ Erreur lors du paiement : `{e}`",
                ephemeral=True
            )

# ⚔️ COG PRINCIPAL
class HollowCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="hollow", help="Lance une tâche Hollow spéciale (infusion Reiatsu).")
    async def hollow(self, ctx):
        prix = 50  # Coût en Reiatsu

        embed = discord.Embed(
            title="🌑 Hollow Among Us",
            description="Une force obscure se manifeste. Vas-tu l’affronter en payant le prix ?",
            color=discord.Color.dark_purple()
        )
        embed.set_footer(text=f"Prix : {prix} points de Reiatsu")

        view = HollowView(ctx, prix)
        await ctx.send(embed=embed, view=view)

    def cog_load(self):
        self.hollow.category = "Hollow"

# 🔌 SETUP DU COG
async def setup(bot: commands.Bot):
    await bot.add_cog(HollowCommand(bot))
    print("✅ Cog chargé : HollowCommand (catégorie = Hollow)")

