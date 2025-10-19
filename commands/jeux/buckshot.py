# ────────────────────────────────────────────────────────────────────────────────
# 📌 buckshot.py — Commande /buckshot et !buckshot (Roulette Buckshot)
# Objectif : Jouer à la "buckshot roulette" contre le bot ou défier un membre (acceptation requise)
# Catégorie : Autre
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Buckshot(commands.Cog):
    """
    Commande /buckshot et !buckshot — Jouer à la Buckshot Roulette
    Usage :
      - !buckshot @membre  -> défier un membre (acceptation requise)
      - !buckshot          -> jouer contre le bot (acceptation automatique)
    Règles :
      - Une seule partie par serveur à la fois
      - Tour par tour, 1 chance sur 6 de perdre à chaque tir
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_games = set()  # guild ids avec partie en cours

    # ───────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ───────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="buckshot",
        description="Défie un membre à la Buckshot Roulette ou joue contre le bot"
    )
    @app_commands.describe(target="Mentionner la personne à défier (optionnel)")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_buckshot(self, interaction: discord.Interaction, target: discord.User = None):
        await interaction.response.defer()
        await self._start_game(interaction, target)

    # ───────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ───────────────────────────────────────────────────────────────────────────
    @commands.command(name="buckshot")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_buckshot(self, ctx: commands.Context, target: discord.Member = None):
        await self._start_game(ctx, target)

    # ───────────────────────────────────────────────────────────────────────────
    # ▶️ Méthode centrale pour gérer la partie
    # ───────────────────────────────────────────────────────────────────────────
    async def _start_game(self, ctx_or_interaction, target):
        is_inter = isinstance(ctx_or_interaction, discord.Interaction)
        guild = getattr(ctx_or_interaction, "guild", None)
        guild_id = guild.id if guild else None

        # Vérifier qu'aucune partie n'est en cours
        if guild_id and guild_id in self.active_games:
            msg = "⚠️ Une partie est déjà en cours sur ce serveur."
            return await (ctx_or_interaction.followup.send if is_inter else ctx_or_interaction.send)(msg)

        # Déterminer joueurs
        challenger = ctx_or_interaction.user if is_inter else ctx_or_interaction.author
        if target is None or target.id == self.bot.user.id:
            opponent = self.bot.user
            vs_bot = True
        else:
            opponent = target
            vs_bot = False

        if not vs_bot and opponent.id == challenger.id:
            msg = "⚠️ Tu ne peux pas te défier toi-même."
            return await (ctx_or_interaction.followup.send if is_inter else ctx_or_interaction.send)(msg)

        # Marquer partie active
        if guild_id:
            self.active_games.add(guild_id)

        try:
            # ────────── Défi / acceptation ──────────
            embed = discord.Embed(
                title="🔫 Buckshot Roulette — Défi",
                description=f"{challenger.mention} défie {opponent.mention if not vs_bot else 'le bot'} !\n"
                            "Appuie sur **Accepter** pour commencer.",
                color=discord.Color.dark_red()
            )

            class ChallengeView(discord.ui.View):
                def __init__(self, timeout=30):
                    super().__init__(timeout=timeout)
                    self.accepted = vs_bot
                    self.cancelled = False

                @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success)
                async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if not vs_bot and interaction.user.id != opponent.id:
                        return await interaction.response.send_message("🚫 Seul le défié peut accepter.", ephemeral=True)
                    for c in self.children:
                        c.disabled = True
                    await interaction.response.edit_message(view=self)
                    self.accepted = True

                @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
                async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
                    if vs_bot:
                        return await interaction.response.send_message("🤖 Le bot ne peut pas refuser.", ephemeral=True)
                    if interaction.user.id != opponent.id:
                        return await interaction.response.send_message("🚫 Seul le défié peut refuser.", ephemeral=True)
                    for c in self.children:
                        c.disabled = True
                    await interaction.response.edit_message(view=self)
                    self.cancelled = True

            view = ChallengeView()
            challenge_msg = await (ctx_or_interaction.followup.send if is_inter else ctx_or_interaction.send)(embed=embed, view=view)

            # Attendre acceptation / refus
            start = asyncio.get_event_loop().time()
            while not view.accepted and not view.cancelled:
                if asyncio.get_event_loop().time() - start > 30:
                    break
                await asyncio.sleep(0.5)

            if view.cancelled:
                return await (ctx_or_interaction.followup.send if is_inter else ctx_or_interaction.send)(f"❌ {opponent.mention} a refusé le défi.")
            if not view.accepted:
                return await (ctx_or_interaction.followup.send if is_inter else ctx_or_interaction.send)("⏰ Défi expiré.")

            # ────────── Partie tour par tour ──────────
            players = [challenger, opponent]
            current = 0

            class FireView(discord.ui.View):
                def __init__(self):
                    super().__init__()
                    self.finished = False
                    self.msg = None

                @discord.ui.button(label="🔘 Tirer", style=discord.ButtonStyle.danger)
                async def fire(self, interaction: discord.Interaction, button: discord.ui.Button):
                    nonlocal current
                    if interaction.user.id != players[current].id:
                        return await interaction.response.send_message("🚫 Ce n'est pas ton tour.", ephemeral=True)
                    button.disabled = True
                    await interaction.response.edit_message(view=self)

                    if random.randint(1, 6) == 1:
                        loser = players[current]
                        winner = players[1 - current]
                        embed = discord.Embed(
                            title="💥 Bang !",
                            description=f"🔴 {loser.mention} a perdu la Buckshot Roulette.\nFélicitations {winner.mention} !",
                            color=discord.Color.red()
                        )
                        await (ctx_or_interaction.followup.send if is_inter else ctx_or_interaction.send)(embed=embed)
                        self.finished = True
                        for c in self.children:
                            c.disabled = True
                        await self.msg.edit(view=self)
                    else:
                        embed = discord.Embed(
                            title="Click. Vide.",
                            description=f"🟢 {players[current].mention} s'en sort.\nTour suivant : {players[1-current].mention}",
                            color=discord.Color.green()
                        )
                        await (ctx_or_interaction.followup.send if is_inter else ctx_or_interaction.send)(embed=embed)
                        current = 1 - current
                        for c in self.children:
                            c.disabled = False
                        await self.msg.edit(view=self)

            fire_view = FireView()
            turn_embed = discord.Embed(
                title="🔫 À toi de jouer",
                description=f"C'est le tour de {players[current].mention}. Appuie sur **Tirer**.",
                color=discord.Color.blurple()
            )
            fire_msg = await (ctx_or_interaction.followup.send if is_inter else ctx_or_interaction.send)(embed=turn_embed, view=fire_view)
            fire_view.msg = fire_msg

        finally:
            if guild_id and guild_id in self.active_games:
                self.active_games.discard(guild_id)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Buckshot(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Autre"
    await bot.add_cog(cog)
