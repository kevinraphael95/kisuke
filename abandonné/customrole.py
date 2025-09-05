# ────────────────────────────────────────────────────────────────────────────────
# 📌 customrole.py — Commande interactive /customrole et !customrole
# Objectif : Permettre aux membres de créer, modifier, supprimer un rôle custom avec couleur (hex ou boutons)
# Catégorie : Autre
# Accès : Tous (sauf clean = admin)
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput
from utils.discord_utils import safe_send, safe_respond, safe_edit
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Couleurs prédéfinies pour boutons
# ────────────────────────────────────────────────────────────────────────────────
PREDEFINED_COLORS = {
    '🔴 Rouge': 0xE74C3C,
    '🟢 Vert': 0x2ECC71,
    '🔵 Bleu': 0x3498DB,
    '🟣 Violet': 0x9B59B6,
    '🟡 Jaune': 0xF1C40F
}

# ────────────────────────────────────────────────────────────────────────────────
# 🎛️ UI Boutons pour couleurs
# ────────────────────────────────────────────────────────────────────────────────
class ColorSelectView(View):
    def __init__(self, bot, user, role_name):
        super().__init__(timeout=120)
        self.bot = bot
        self.user = user
        self.role_name = role_name

        for label, color in PREDEFINED_COLORS.items():
            self.add_item(ColorButton(label, color, self))

        # Bouton pour hex personnalisé
        self.add_item(CustomHexButton(self))

class ColorButton(Button):
    def __init__(self, label, color, parent_view):
        super().__init__(style=discord.ButtonStyle.secondary, label=label)
        self.color = color
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        await handle_role_creation(interaction, self.parent_view.user, self.parent_view.role_name, self.color)
        self.parent_view.stop()

class CustomHexButton(Button):
    def __init__(self, parent_view):
        super().__init__(style=discord.ButtonStyle.primary, label='Hex perso')
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        modal = HexInputModal(self.parent_view.user, self.parent_view.role_name)
        await interaction.response.send_modal(modal)
        self.parent_view.stop()

class HexInputModal(Modal):
    def __init__(self, user, role_name):
        super().__init__(title="Rôle couleur Hex")
        self.user = user
        self.role_name = role_name
        self.hex_input = TextInput(label="Code couleur (#RRGGBB)", placeholder="#FF0000")
        self.add_item(self.hex_input)

    async def on_submit(self, interaction: discord.Interaction):
        hex_code = self.hex_input.value.strip()
        try:
            if hex_code.startswith('#') and len(hex_code) == 7:
                color = int(hex_code[1:], 16)
                await handle_role_creation(interaction, self.user, self.role_name, color)
            else:
                await safe_respond(interaction, "❌ Format invalide, utilisez #RRGGBB", ephemeral=True)
        except Exception as e:
            print(f"[HEX ERROR] {e}")
            await safe_respond(interaction, "❌ Erreur lors de la création du rôle", ephemeral=True)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Fonction de création/mise à jour du rôle
# ────────────────────────────────────────────────────────────────────────────────
async def handle_role_creation(interaction: discord.Interaction, user, role_name, color):
    guild = interaction.guild
    # Vérifier si le rôle custom existe déjà
    resp = supabase.table('custom_roles').select('*').eq('guild_id', str(guild.id)).eq('user_id', str(user.id)).execute()
    data = resp.data if hasattr(resp, 'data') else []

    if data:
        # Mise à jour rôle existant
        role_id = int(data[0]['role_id'])
        role = guild.get_role(role_id)
        if role:
            await role.edit(name=role_name, color=discord.Color(color))
            await safe_respond(interaction, f"✅ Rôle custom mis à jour pour {user.mention}")
        supabase.table('custom_roles').update({'role_name': role_name, 'role_color': f'#{color:06X}'}).eq('id', data[0]['id']).execute()
    else:
        # Création rôle
        role = await guild.create_role(name=role_name, color=discord.Color(color))
        await user.add_roles(role)
        supabase.table('custom_roles').insert({'guild_id': str(guild.id), 'user_id': str(user.id), 'role_id': str(role.id), 'role_name': role_name, 'role_color': f'#{color:06X}'}).execute()
        await safe_respond(interaction, f"✅ Rôle custom créé pour {user.mention}")

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class CustomRole(commands.Cog):
    """
    Commande /customrole et !customrole — Gestion des rôles custom
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH CREATE
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="customrole", description="Créer ou modifier un rôle custom")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_customrole(self, interaction: discord.Interaction, name: str):
        """Crée ou modifie ton rôle custom"""
        view = ColorSelectView(self.bot, interaction.user, name)
        await interaction.response.send_message(f"Choisis une couleur pour ton rôle **{name}** :", view=view, ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH DELETE
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="customrole_delete", description="Supprime ton rôle custom")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_customrole_delete(self, interaction: discord.Interaction):
        resp = supabase.table('custom_roles').select('*').eq('guild_id', str(interaction.guild.id)).eq('user_id', str(interaction.user.id)).execute()
        data = resp.data if hasattr(resp, 'data') else []
        if not data:
            await safe_respond(interaction, "❌ Tu n'as pas de rôle custom", ephemeral=True)
            return
        role_id = int(data[0]['role_id'])
        role = interaction.guild.get_role(role_id)
        if role:
            await role.delete()
        supabase.table('custom_roles').delete().eq('id', data[0]['id']).execute()
        await safe_respond(interaction, f"✅ Rôle custom supprimé pour {interaction.user.mention}")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH CLEAN (ADMIN)
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="customrole_clean", description="Supprime tous les rôles custom du serveur")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_customrole_clean(self, interaction: discord.Interaction):
        resp = supabase.table('custom_roles').select('*').eq('guild_id', str(interaction.guild.id)).execute()
        data = resp.data if hasattr(resp, 'data') else []
        count = 0
        for entry in data:
            role = interaction.guild.get_role(int(entry['role_id']))
            if role:
                await role.delete()
                count += 1
        supabase.table('custom_roles').delete().eq('guild_id', str(interaction.guild.id)).execute()
        await safe_respond(interaction, f"✅ {count} rôles custom supprimés du serveur")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX (redirection)
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="customrole")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_customrole(self, ctx: commands.Context, *, name: str):
        fake_inter = type('I', (), {'user': ctx.author, 'guild': ctx.guild, 'response': type('R', (), {'send_message': lambda self, content=None, view=None, ephemeral=False: safe_send(ctx.channel, content)})()})()
        await self.slash_customrole.callback(self, fake_inter, name)

    @commands.command(name="customrole_delete")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_customrole_delete(self, ctx: commands.Context):
        fake_inter = type('I', (), {'user': ctx.author, 'guild': ctx.guild, 'response': type('R', (), {'send_message': lambda self, content=None, view=None, ephemeral=False: safe_send(ctx.channel, content)})()})()
        await self.slash_customrole_delete.callback(self, fake_inter)

    @commands.command(name="customrole_clean")
    @commands.has_permissions(administrator=True)
    async def prefix_customrole_clean(self, ctx: commands.Context):
        fake_inter = type('I', (), {'user': ctx.author, 'guild': ctx.guild, 'response': type('R', (), {'send_message': lambda self, content=None, view=None, ephemeral=False: safe_send(ctx.channel, content)})()})()
        await self.slash_customrole_clean.callback(self, fake_inter)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = CustomRole(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Autre"
    await bot.add_cog(cog)
