# ────────────────────────────────────────────────────────────────────────────────
# 📌 steamkey.py — Commande interactive !steamkey avec embed + bouton miser
# Objectif : Tenter de gagner une clé Steam contre des Reiatsu via un bouton
# Catégorie : Reiatsu
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
import random
import os
from supabase import create_client, Client
from discord_utils import safe_send, safe_respond  # Fonctions anti-429 pour éviter les ratelimits

# ────────────────────────────────────────────────────────────────────────────────
# 📂 CONSTANTES
# ────────────────────────────────────────────────────────────────────────────────
REIATSU_COST = 30
WIN_CHANCE = 0.01  # 1%

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 View pour le bouton miser
# ────────────────────────────────────────────────────────────────────────────────
class SteamKeyView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=120)  # 2 minutes timeout
        self.author_id = author_id
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ Ce bouton n'est pas pour toi.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Miser 30 Reiatsu", style=discord.ButtonStyle.green)
    async def bet_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True
        await interaction.response.edit_message(view=self)
        self.value = True
        self.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal — SteamKey
# ────────────────────────────────────────────────────────────────────────────────
class SteamKey(commands.Cog):
    """
    Commande !steamkey — Tente ta chance pour gagner une clé Steam en dépensant des Reiatsu via un bouton.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        print("[SteamKey] Cog chargé correctement.")

    # ────────────────────────────────────────────────────────────────────────────────
    # 🔑 Fonction interne commune — appelée après clic sur miser
    # ────────────────────────────────────────────────────────────────────────────────
    async def _try_win_key(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # Récupération des infos Reiatsu du joueur
        response = supabase.table("reiatsu") \
            .select("*") \
            .eq("user_id", user_id) \
            .single() \
            .execute()

        if not response.data:
            await interaction.followup.send("❌ Vous n'avez pas encore de Reiatsu enregistré.", ephemeral=True)
            return

        reiatsu_amount = response.data["points"]

        if reiatsu_amount < REIATSU_COST:
            await interaction.followup.send(f"❌ Il vous faut **{REIATSU_COST} Reiatsu** pour miser.", ephemeral=True)
            return

        # Déduction immédiate des Reiatsu
        supabase.table("reiatsu") \
            .update({"points": reiatsu_amount - REIATSU_COST}) \
            .eq("user_id", user_id) \
            .execute()

        # Tentative de gain
        if random.random() <= WIN_CHANCE:
            keys_data = supabase.table("steam_keys").select("*").limit(1).execute()

            if not keys_data.data:
                embed = discord.Embed(
                    title="Jeu Steam Key - Résultat",
                    description="🎉 Vous avez gagné ! Mais il n'y a malheureusement plus de clés disponibles.",
                    color=discord.Color.gold()
                )
            else:
                key = keys_data.data[0]

                # Suppression de la clé gagnée de la base
                supabase.table("steam_keys").delete().eq("id", key["id"]).execute()

                embed = discord.Embed(
                    title="🎉 Félicitations ! Vous avez gagné une clé Steam !",
                    color=discord.Color.green()
                )
                embed.add_field(name="Jeu", value=key["game_name"], inline=False)
                embed.add_field(name="Lien Steam", value=f"[Clique ici]({key['steam_url']})", inline=False)
                embed.add_field(name="Clé Steam", value=f"`{key['steam_key']}`", inline=False)
        else:
            embed = discord.Embed(
                title="Jeu Steam Key - Résultat",
                description="❌ Désolé, vous n'avez pas gagné cette fois. Retentez votre chance !",
                color=discord.Color.red()
            )

        await interaction.followup.send(embed=embed)

    # ────────────────────────────────────────────────────────────────────────────────
    # ⌨️ Commande préfixe
    # ────────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="steamkey",
        aliases=["sk"],
        help="🎮 Tente de gagner une clé Steam en dépensant des Reiatsu.",
        description="Mise 30 Reiatsu pour tenter de remporter une clé Steam."
    )
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def steamkey(self, ctx: commands.Context):
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        except Exception as e:
            print(f"[ERREUR suppression message !steamkey] {e}")

        # Récupérer stats clés pour l'embed d'intro
        keys_resp = supabase.table("steam_keys").select("id, game_name").execute()
        nb_keys = len(keys_resp.data) if keys_resp.data else 0
        games = set(k["game_name"] for k in keys_resp.data) if keys_resp.data else set()

        embed = discord.Embed(
            title="🎮 Jeu Steam Key",
            description=f"Miser {REIATSU_COST} Reiatsu pour avoir une très faible chance de gagner une clé Steam.",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Nombre de clés à gagner", value=str(nb_keys), inline=True)
        embed.add_field(name="Jeux possibles à gagner", value=", ".join(games) if games else "Aucun", inline=True)
        embed.set_footer(text="Vous avez 2 minutes pour miser.")

        view = SteamKeyView(ctx.author.id)
        await ctx.send(embed=embed, view=view)

        # Attendre le clic sur le bouton ou timeout
        await view.wait()

        if view.value:
            # Lancer la tentative de gain
            await self._try_win_key(ctx)
        else:
            # Timeout ou bouton non cliqué, désactiver le bouton
            for child in view.children:
                child.disabled = True
            await ctx.send("⏰ Temps écoulé, la mise a été annulée.")

    # ────────────────────────────────────────────────────────────────────────────────
    # 💬 Commande slash
    # ────────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="steamkey",
        description="🎮 Tente de gagner une clé Steam en dépensant des Reiatsu."
    )
    async def steamkey_slash(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(thinking=True)

            # Récupérer stats clés pour l'embed d'intro
            keys_resp = supabase.table("steam_keys").select("id, game_name").execute()
            nb_keys = len(keys_resp.data) if keys_resp.data else 0
            games = set(k["game_name"] for k in keys_resp.data) if keys_resp.data else set()

            embed = discord.Embed(
                title="🎮 Jeu Steam Key",
                description=f"Miser {REIATSU_COST} Reiatsu pour avoir une très faible chance de gagner une clé Steam.",
                color=discord.Color.blurple()
            )
            embed.add_field(name="Nombre de clés à gagner", value=str(nb_keys), inline=True)
            embed.add_field(name="Jeux possibles à gagner", value=", ".join(games) if games else "Aucun", inline=True)
            embed.set_footer(text="Vous avez 2 minutes pour miser.")

            view = SteamKeyView(interaction.user.id)
            await interaction.followup.send(embed=embed, view=view)

            await view.wait()

            if view.value:
                await self._try_win_key(interaction)
            else:
                # Timeout : on édite le message pour désactiver le bouton si possible
                for child in view.children:
                    child.disabled = True

                # interaction.response a déjà été envoyée => on doit éditer followup
                await interaction.followup.edit_message(message_id=interaction.message.id, view=view)
                await interaction.followup.send("⏰ Temps écoulé, la mise a été annulée.", ephemeral=True)

        except Exception as e:
            print(f"[ERREUR /steamkey] {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("❌ Une erreur est survenue.", ephemeral=True)
                else:
                    await interaction.followup.send("❌ Une erreur est survenue.", ephemeral=True)
            except:
                pass

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SteamKey(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)




