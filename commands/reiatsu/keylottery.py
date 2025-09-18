# ────────────────────────────────────────────────────────────────────────────────
# 📌 keylottery.py — Commande interactive /scratchkey et !scratchkey
# Objectif : Ticket à gratter avec 10 boutons et remise en jeu d'une clé Steam
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
WIN_CHANCE = 0.1  # 10% de chance de gagner

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Ticket à gratter
# ────────────────────────────────────────────────────────────────────────────────
class ScratchTicketView(View):
    def __init__(self, author_id: int, message: discord.Message = None):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.message = message
        self.value = None
        self.last_interaction = None
        self.winning_button = random.randint(0, NB_BUTTONS - 1)
        self.double_button = random.randint(0, NB_BUTTONS - 1)
        while self.double_button == self.winning_button:
            self.double_button = random.randint(0, NB_BUTTONS - 1)

        # ⚠️ Ajouter les boutons du ticket
        for i in range(NB_BUTTONS):
            self.add_item(ScratchButton(i, self))

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
            embed.set_footer(text="⏳ Temps écoulé. Relance /scratchkey pour retenter ta chance.")
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
            msg = f"🎉 Tu as gagné une clé Steam !"
        elif self.index == self.parent_view.double_button:
            result = "double"
            color = discord.Color.gold()
            msg = f"💎 Jackpot ! Tu gagnes **le double** de ta mise !"
        else:
            result = "lose"
            color = discord.Color.red()
            msg = f"😢 Perdu ! Pas de chance cette fois."

        embed = discord.Embed(title="🎰 Ticket à Gratter", description=msg, color=color)
        embed.set_footer(text="Relance /scratchkey pour tenter à nouveau.")
        await interaction.response.edit_message(embed=embed, view=self.parent_view)
        self.parent_view.value = result
        self.parent_view.last_interaction = interaction
        self.parent_view.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI — Confirmation + choix de clé
# ────────────────────────────────────────────────────────────────────────────────
class ConfirmKeyView(View):
    def __init__(self, author_id: int, keys_dispo: list, message: discord.Message, current_index: int = 0):
        super().__init__(timeout=120)
        self.author_id = author_id
        self.keys_dispo = keys_dispo
        self.index = current_index
        self.message = message
        self.choice = None
        self.switch_count = 0
        self.max_switches = 3

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author_id

    @property
    def current_key(self):
        return self.keys_dispo[self.index]

    def build_embed(self):
        embed = discord.Embed(
            title="🎉 Tu as gagné une clé Steam !",
            description="Choisis la clé qui te convient le mieux.\n⚠️ Tu peux cliquer sur **Autre jeu** jusqu’à 3 fois.",
            color=discord.Color.green()
        )
        embed.add_field(name="🎮 Jeu", value=self.current_key["game_name"], inline=False)
        embed.add_field(name="🔗 Lien Steam", value=f"[Voir sur Steam]({self.current_key['steam_url']})", inline=False)
        embed.set_footer(text=f"✅ : Prendre | 🎲 : Autre jeu ({self.switch_count}/{self.max_switches}) | ❌ : Refuser")
        return embed

    async def refresh_embed(self, interaction: discord.Interaction):
        await safe_edit(self.message, embed=self.build_embed(), view=self)
        await interaction.response.defer()

    @discord.ui.button(label="✅ Prendre cette clé", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: Button):
        self.choice = "accept"
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="🎲 Autre jeu", style=discord.ButtonStyle.blurple)
    async def other_game(self, interaction: discord.Interaction, button: Button):
        self.switch_count += 1
        if self.switch_count >= self.max_switches:
            button.disabled = True
        self.index = (self.index + 1) % len(self.keys_dispo)
        await self.refresh_embed(interaction)

    @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        self.choice = "reject"
        await interaction.response.defer()
        self.stop()

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class ScratchKey(commands.Cog):
    """Commande /scratchkey et !scratchkey — Ticket à gratter interactif avec clés Steam"""
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

    async def _get_all_steam_keys(self):
        try:
            resp = supabase.table("steam_keys").select("*").eq("won", False).execute()
            return resp.data or []
        except Exception as e:
            print(f"[ERREUR Supabase _get_all_steam_keys] {e}")
            return []

    async def _mark_steam_key_won(self, key_id: int, winner: str):
        try:
            supabase.table("steam_keys").update({"won": True, "winner": winner}).eq("id", key_id).execute()
        except Exception as e:
            print(f"[ERREUR Supabase _mark_steam_key_won] {e}")

    async def _send_ticket(self, channel, user, user_id: int):
        reiatsu_points = await self._get_reiatsu(user_id)
        keys_dispo = await self._get_all_steam_keys()
        jeux = ", ".join([k["game_name"] for k in keys_dispo[:5]]) or "Aucun"
        if len(keys_dispo) > 5:
            jeux += "…"
        embed = discord.Embed(
            title="🎟️ Ticket à gratter",
            description=(
                f"**Reiatsu possédé** : **{reiatsu_points}**\n"
                f"**Prix du ticket** : **{SCRATCH_COST}**\n"
                f"**🔑 Nombre de clés à gagner** : **{len(keys_dispo)}**\n"
                f"**🎮 Jeux gagnables** : {jeux}\n\n"
                f"**Comment jouer ?** : Appuie sur **Miser et jouer** pour acheter un ticket et révéler 10 boutons.\n"
                f"Clique sur l’un des 10 boutons 🎟️ pour découvrir ton gain.\n"
                f" • Si tu trouves la clé 🔑 tu gagnes une **clé Steam**.\n"
                f" • Si tu trouves le jackpot 💎 tu gagnes **le double de ta mise**.\n"
                f" • Sinon... tu repars les mains vides 😢 !"
            ),
            color=discord.Color.blurple()
        )
        view = ScratchTicketView(user_id)
        message = await safe_send(channel, embed=embed, view=view)
        view.message = message
        return view

    async def _handle_result(self, interaction_or_ctx, result: str, user_id: str):
        reiatsu_points = await self._get_reiatsu(user_id)
        if result == "win":
            await self._update_reiatsu(user_id, reiatsu_points + SCRATCH_COST)
        elif result == "double":
            await self._update_reiatsu(user_id, reiatsu_points + SCRATCH_COST * 2)

        if result in ["win", "double"]:
            keys_dispo = await self._get_all_steam_keys()
            if not keys_dispo:
                return await safe_send(interaction_or_ctx.channel, "⛔ Aucune clé Steam disponible.")
            msg = await safe_send(interaction_or_ctx.channel, "🎁 Recherche d'une clé Steam en cours...")
            view = ConfirmKeyView(interaction_or_ctx.user.id, keys_dispo, msg)
            await safe_edit(msg, embed=view.build_embed(), view=view)
            await view.wait()
            if view.choice == "accept":
                chosen = view.current_key
                await self._mark_steam_key_won(chosen["id"], interaction_or_ctx.user.name)
                try:
                    await interaction_or_ctx.user.send(
                        f"🎁 **Clé Steam pour {chosen['game_name']}**\n`{chosen['steam_key']}`"
                    )
                    await safe_edit(msg, embed=discord.Embed(title="✅ Clé envoyée en DM !", color=discord.Color.green()), view=None)
                except discord.Forbidden:
                    await safe_edit(msg, embed=discord.Embed(title="⚠️ Impossible d'envoyer un DM.", color=discord.Color.orange()), view=None)
            elif view.choice == "reject":
                await safe_edit(msg, embed=discord.Embed(title="🔄 Clé remise en jeu pour les autres joueurs.", color=discord.Color.blurple()), view=None)

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
                if view.value:
                    await self._handle_result(view.last_interaction, view.value, str(interaction.user.id))
        except Exception as e:
            print(f"[ERREUR /scratchkey] {e}")
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
                if view.value:
                    class DummyInteraction:
                        def __init__(self, user, channel):
                            self.user, self.channel = user, channel
                    await self._handle_result(DummyInteraction(ctx.author, ctx.channel), view.value, str(ctx.author.id))
        except Exception as e:
            print(f"[ERREUR !scratchkey] {e}")
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
