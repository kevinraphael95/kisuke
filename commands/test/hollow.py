# ────────────────────────────────────────────────────────────────────────────────
# 📌 combat_hollow.py — Commande interactive !combat_hollow
# Objectif : Lancer un combat interactif contre un Hollow avec choix tactiques et chance
# Catégorie : Bleach
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import random

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ Vue interactive pour gérer le combat
# ────────────────────────────────────────────────────────────────────────────────
class CombatView(View):
    def __init__(self, ctx, player_hp=100, hollow_hp=80):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.player_hp = player_hp
        self.hollow_hp = hollow_hp
        self.message = None
        self.ended = False

    async def send_initial(self):
        embed = self._get_embed()
        self.message = await self.ctx.send(embed=embed, view=self)

    def _get_embed(self):
        embed = discord.Embed(
            title="⚔️ Combat contre un Hollow",
            description=(
                f"Ton HP: **{self.player_hp}**\n"
                f"Hollow HP: **{self.hollow_hp}**\n\n"
                "Choisis ton action en cliquant sur un bouton ci-dessous :\n"
                "⚔️ Attaque — 🛡 Défense — 💨 Esquive"
            ),
            color=discord.Color.orange()
        )
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Ce combat n'est pas pour toi !", ephemeral=True)
            return False
        return True

    def _resolve_turn(self, player_choice: str):
        reactions = ["⚔️", "🛡", "💨"]
        hollow_choice = random.choice(reactions)

        dmg_to_hollow = 0
        dmg_to_player = 0
        resultat = ""

        if player_choice == "⚔️":
            if hollow_choice == "🛡":
                dmg_to_hollow = random.randint(5, 10)
                resultat = f"Tu attaques, le Hollow défend. Tu infliges {dmg_to_hollow} dégâts."
            elif hollow_choice == "💨":
                dmg_to_hollow = 0
                resultat = "Tu attaques, mais le Hollow esquive ton attaque !"
            else:  # hollow attaque
                dmg_to_hollow = random.randint(5, 15)
                dmg_to_player = random.randint(5, 15)
                resultat = f"Vous vous attaquez ! Tu infliges {dmg_to_hollow} dégâts mais tu prends {dmg_to_player} dégâts."
        elif player_choice == "🛡":
            if hollow_choice == "💨":
                dmg_to_player = random.randint(5, 10)
                resultat = f"Tu défends, mais le Hollow esquive et t'attaque fort. Tu prends {dmg_to_player} dégâts."
            elif hollow_choice == "⚔️":
                dmg_to_player = random.randint(5, 10)
                resultat = f"Tu défends contre l'attaque du Hollow, tu prends {dmg_to_player} dégâts réduits."
            else:
                resultat = "Vous êtes tous les deux sur la défensive, aucun dégât."
        else:  # esquive
            if hollow_choice == "⚔️":
                dmg_to_hollow = 0
                resultat = "Tu esquives l'attaque du Hollow avec succès !"
            elif hollow_choice == "🛡":
                resultat = "Tu esquives pendant que le Hollow défend, pas d'attaque."
            else:
                dmg_to_player = random.randint(5, 15)
                resultat = f"Tu esquives, mais le Hollow t'attaque de côté et inflige {dmg_to_player} dégâts."

        self.player_hp -= dmg_to_player
        self.hollow_hp -= dmg_to_hollow
        return resultat, hollow_choice

    async def end_combat(self, message: discord.Message, resultat: str):
        self.ended = True
        self.clear_items()
        if self.player_hp <= 0:
            embed = discord.Embed(
                title="💀 Défaite",
                description=f"{resultat}\nTu as été vaincu par le Hollow...",
                color=discord.Color.red()
            )
        elif self.hollow_hp <= 0:
            embed = discord.Embed(
                title="🎉 Victoire",
                description=f"{resultat}\nBravo, tu as vaincu le Hollow !",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Combat terminé",
                description="Le combat s'est terminé prématurément.",
                color=discord.Color.dark_grey()
            )
        await message.edit(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="⚔️ Attaque", style=discord.ButtonStyle.red)
    async def attack(self, interaction: discord.Interaction, button: Button):
        if self.ended:
            await interaction.response.send_message("Le combat est terminé.", ephemeral=True)
            return
        resultat, hollow_choice = self._resolve_turn("⚔️")
        embed = self._get_embed()
        embed.description += f"\n\n**Tour:**\nTu as choisi ⚔️ Attaque\nLe Hollow a choisi {hollow_choice}\n\n{resultat}"
        await interaction.response.edit_message(embed=embed, view=self)

        if self.player_hp <= 0 or self.hollow_hp <= 0:
            await self.end_combat(interaction.message, resultat)

    @discord.ui.button(label="🛡 Défense", style=discord.ButtonStyle.blurple)
    async def defend(self, interaction: discord.Interaction, button: Button):
        if self.ended:
            await interaction.response.send_message("Le combat est terminé.", ephemeral=True)
            return
        resultat, hollow_choice = self._resolve_turn("🛡")
        embed = self._get_embed()
        embed.description += f"\n\n**Tour:**\nTu as choisi 🛡 Défense\nLe Hollow a choisi {hollow_choice}\n\n{resultat}"
        await interaction.response.edit_message(embed=embed, view=self)

        if self.player_hp <= 0 or self.hollow_hp <= 0:
            await self.end_combat(interaction.message, resultat)

    @discord.ui.button(label="💨 Esquive", style=discord.ButtonStyle.gray)
    async def dodge(self, interaction: discord.Interaction, button: Button):
        if self.ended:
            await interaction.response.send_message("Le combat est terminé.", ephemeral=True)
            return
        resultat, hollow_choice = self._resolve_turn("💨")
        embed = self._get_embed()
        embed.description += f"\n\n**Tour:**\nTu as choisi 💨 Esquive\nLe Hollow a choisi {hollow_choice}\n\n{resultat}"
        await interaction.response.edit_message(embed=embed, view=self)

        if self.player_hp <= 0 or self.hollow_hp <= 0:
            await self.end_combat(interaction.message, resultat)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CombatHollow(commands.Cog):
    """Commande !combat_hollow — Combat interactif contre un Hollow"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_combats = set()

    @commands.command(
        name="combat_hollow",
        help="Lance un combat contre un Hollow avec choix tactiques.",
        description="Commande interactive où tu choisis Attaque, Défense ou Esquive pour vaincre un Hollow."
    )
    async def combat_hollow(self, ctx: commands.Context):
        if ctx.author.id in self.active_combats:
            await ctx.reply("🛑 Tu es déjà en combat contre un Hollow, finis-le avant d'en commencer un nouveau !", mention_author=True)
            return

        self.active_combats.add(ctx.author.id)
        try:
            view = CombatView(ctx)
            await view.send_initial()
            await view.wait()
        finally:
            self.active_combats.remove(ctx.author.id)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CombatHollow(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "bleach"
    await bot.add_cog(cog)
