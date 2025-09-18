# ────────────────────────────────────────────────────────────────────────────────
# 📌 keylottery.py — Commande interactive /keylottery et !keylottery
# Objectif : Ticket à gratter avec 10 boutons, mise uniquement après clic
# Catégorie : Reiatsu
# Accès : Public
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
import random
from utils.supabase_client import supabase
from utils.discord_utils import safe_send, safe_edit, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Constantes
# ────────────────────────────────────────────────────────────────────────────────
SCRATCH_COST = 300
NB_BUTTONS = 10

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Ticket à gratter
# ────────────────────────────────────────────────────────────────────────────────
class ScratchTicketView(View):
    def __init__(self, author_id: int, message: discord.Message = None, keys_available: bool = True):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.message = message
        self.value = None
        self.last_interaction = None
        self.winning_button = random.randint(0, NB_BUTTONS - 1)
        self.double_button = random.randint(0, NB_BUTTONS - 1)
        while self.double_button == self.winning_button:
            self.double_button = random.randint(0, NB_BUTTONS - 1)

        # Si pas de clé dispo, désactiver le bouton directement
        if not keys_available:
            for child in self.children:
                if isinstance(child, Button):
                    child.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await safe_respond(interaction, "❌ Ce ticket n'est pas pour toi.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            embed = self.message.embeds[0]
            embed.set_footer(text="⏳ Temps écoulé. Relance /keylottery pour retenter ta chance.")
            await safe_edit(self.message, embed=embed, view=self)

    @discord.ui.button(label=f"Miser {SCRATCH_COST} Reiatsu et jouer", style=discord.ButtonStyle.green)
    async def bet_button(self, interaction: discord.Interaction, button: Button):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.value = True
        self.last_interaction = interaction
        self.stop()

class ScratchButton(Button):
    def __init__(self, index: int, parent: ScratchTicketView):
        super().__init__(label=f"🎟️ {index+1}", style=discord.ButtonStyle.blurple)
        self.index = index
        self.parent_view = parent

    async def callback(self, interaction: discord.Interaction):
        for child in self.parent_view.children:
            child.disabled = True
        if self.index == self.parent_view.winning_button:
            result = "win"
            color = discord.Color.green()
            msg = f"🎉 Tu as gagné une clé Steam ! (Mise x1)"
        elif self.index == self.parent_view.double_button:
            result = "double"
            color = discord.Color.gold()
            msg = f"💎 Jackpot ! Tu gagnes **le double** de ta mise !"
        else:
            result = "lose"
            color = discord.Color.red()
            msg = f"😢 Perdu ! Pas de chance cette fois."

        embed = discord.Embed(title="🎰 Ticket à Gratter", description=msg, color=color)
        embed.set_footer(text="Relance /keylottery pour tenter à nouveau.")
        await interaction.response.edit_message(embed=embed, view=self.parent_view)
        self.parent_view.value = result
        self.parent_view.last_interaction = interaction
        self.parent_view.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ScratchKey(commands.Cog):
    """Commande /keylottery et !keylottery — Ticket à gratter interactif"""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _get_reiatsu(self, user_id: str) -> int:
        try:
            resp = supabase.table("reiatsu").select("points").eq("user_id", user_id).single().execute()
            return resp.data["points"] if resp.data else 0
        except Exception as e:
            print(f"[ERREUR Supabase _get_reiatsu] {e}")
            return 0

    async def _update_reiatsu(self, user_id: str, new_points: int):
        try:
            supabase.table("reiatsu").update({"points": new_points}).eq("user_id", user_id).execute()
        except Exception as e:
            print(f"[ERREUR Supabase _update_reiatsu] {e}")

    async def _send_ticket(self, channel, user, user_id: int):
        reiatsu_points = await self._get_reiatsu(user_id)

        # Récupérer les clés Steam disponibles
        try:
            resp = supabase.table("steamkeys").select("game").eq("used", False).execute()
            available_keys = resp.data if resp.data else []
        except Exception as e:
            print(f"[ERREUR Supabase _send_ticket] {e}")
            available_keys = []

        keys_count = len(available_keys)
        games_preview = ", ".join([k["game"] for k in available_keys[:5]])
        if len(available_keys) > 5:
            games_preview += ", ..."

        embed = discord.Embed(
            title="🎟️ Ticket à gratter",
            description=(
                f"**Reiatsu possédé** : **{reiatsu_points}**\n"
                f"**Prix du ticket** : **{SCRATCH_COST}**\n"
                f"**Gains potentiels** : Clé Steam (1/10), Doubler sa mise (1/10), Rien (8/10)\n"
                f"**Clés restantes** : **{keys_count}**\n"
                f"**Jeux en loterie** : {games_preview if games_preview else 'Aucun 😢'}\n\n"
                f"**Comment jouer ?** : Appuie sur **Miser et jouer** pour acheter un ticket et révéler 10 boutons.\n"
                f"Clique sur l’un des 10 boutons 🎟️ pour découvrir ton gain.\n"
                f" • Si tu trouves la clé 🔑 tu gagnes une **clé Steam**.\n"
                f" • Si tu trouves le jackpot 💎 tu gagnes **le double de ta mise**.\n"
                f" • Sinon... tu repars les mains vides 😢 !"
            ),
            color=discord.Color.blurple()
        )
        if keys_count == 0:
            embed.set_footer(text="🚫 Plus de clés disponibles pour le moment.")

        view = ScratchTicketView(user_id, keys_available=keys_count > 0)
        message = await safe_send(channel, embed=embed, view=view)
        view.message = message
        return view

    async def _handle_result(self, interaction_or_ctx, result: str, user_id: str):
        reiatsu_points = await self._get_reiatsu(user_id)
        if result == "win":
            await self._update_reiatsu(user_id, reiatsu_points + SCRATCH_COST)
        elif result == "double":
            await self._update_reiatsu(user_id, reiatsu_points + SCRATCH_COST * 2)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="keylottery", description="Ticket à gratter : tente ta chance pour gagner des clés ou du Reiatsu")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.user.id))
    async def slash_scratchkey(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            view = await self._send_ticket(interaction.channel, interaction.user, interaction.user.id)
            await view.wait()
            if view.value:
                reiatsu_points = await self._get_reiatsu(str(interaction.user.id))
                if reiatsu_points < SCRATCH_COST:
                    return await safe_respond(interaction, f"❌ Pas assez de Reiatsu ! Il te faut {SCRATCH_COST}.", ephemeral=True)
                await self._update_reiatsu(str(interaction.user.id), reiatsu_points - SCRATCH_COST)
                button_view = ScratchTicketView(interaction.user.id)
                await button_view.wait()
                if button_view.value:
                    await self._handle_result(view.last_interaction, button_view.value, str(interaction.user.id))
        except Exception as e:
            print(f"[ERREUR /keylottery] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="keylottery", aliases=["kl"])
    @commands.cooldown(1, 10.0, commands.BucketType.user)
    async def prefix_scratchkey(self, ctx: commands.Context):
        try:
            view = await self._send_ticket(ctx.channel, ctx.author, ctx.author.id)
            await view.wait()
            if view.value:
                reiatsu_points = await self._get_reiatsu(str(ctx.author.id))
                if reiatsu_points < SCRATCH_COST:
                    return await safe_send(ctx.channel, f"❌ Pas assez de Reiatsu ! Il te faut {SCRATCH_COST}.")
                await self._update_reiatsu(str(ctx.author.id), reiatsu_points - SCRATCH_COST)
                button_view = ScratchTicketView(ctx.author.id)
                await button_view.wait()
                if button_view.value:
                    class DummyInteraction:
                        def __init__(self, user, channel):
                            self.user, self.channel = user, channel
                    await self._handle_result(DummyInteraction(ctx.author, ctx.channel), button_view.value, str(ctx.author.id))
        except Exception as e:
            print(f"[ERREUR !keylottery] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ScratchKey(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Reiatsu"
    await bot.add_cog(cog)
