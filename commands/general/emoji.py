# ────────────────────────────────────────────────────────────────────────────────
# 📌 emoji_command.py — Commande interactive !emoji / !e et /emoji
# Objectif : Afficher un ou plusieurs emojis du serveur via une commande
# Catégorie : 🎉 Fun
# Accès : Public
# Cooldown : 1 utilisation / 3 sec / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send

# ────────────────────────────────────────────────────────────────────────────────
# 🎮 View pour la pagination
# ────────────────────────────────────────────────────────────────────────────────
class EmojiPaginator(discord.ui.View):
    def __init__(self, pages: list[discord.Embed], timeout: int = 90):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.index = 0

    async def update(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.pages[self.index], view=self)

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index - 1) % len(self.pages)
        await self.update(interaction)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index = (self.index + 1) % len(self.pages)
        await self.update(interaction)

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class EmojiCommand(commands.Cog):
    """Commande !emoji / !e et /emoji — Affiche un ou plusieurs emojis du serveur."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Fonctions internes
    # ────────────────────────────────────────────────────────────────────────────
    def _find_emojis(self, emoji_names: tuple[str], guild: discord.Guild):
        """Retourne deux listes : (trouvés, introuvables)."""
        found, not_found = [], []
        for raw_name in emoji_names:
            # 🔹 On garde le nom exact (pas de strip)
            name = raw_name.lower().replace(":", "")  
            match = discord.utils.find(lambda e: e.name.lower() == name and e.available, guild.emojis)
            if match:
                found.append(str(match))
            else:
                not_found.append(raw_name)
        return found, not_found


    def _build_pages(self, guilds: list[discord.Guild]) -> list[discord.Embed]:
        """Construit les pages d'emojis animés, une page par serveur (ou plusieurs si nécessaire)."""
        pages = []
        for g in guilds:
            animated = [str(e) for e in g.emojis if e.animated and e.available]
            if not animated:
                continue

            # Découpe en paquets de 40 pour éviter le dépassement
            chunks = [animated[i:i+40] for i in range(0, len(animated), 40)]
            for i, chunk in enumerate(chunks, start=1):
                embed = discord.Embed(
                    title=f"🎭 Emojis animés — {g.name}",
                    description=" ".join(chunk),
                    color=discord.Color.orange()
                )
                if len(chunks) > 1:
                    embed.set_footer(text=f"Page {i}/{len(chunks)} pour {g.name}")
                pages.append(embed)
        return pages

    async def _display_emojis(self, channel, guild, emoji_names: tuple[str]):
        """Affiche soit des emojis précis, soit tous les animés paginés de tous les serveurs."""
        try:
            if emoji_names:
                # Recherche ciblée dans le serveur actuel
                found, not_found = self._find_emojis(emoji_names, guild)
                if found:
                    await safe_send(channel, " ".join(found))
                if not_found:
                    await safe_send(channel, f"❌ Emojis introuvables : {', '.join(f'`{n}`' for n in not_found)}")
            else:
                # Pagination sur tous les serveurs où le bot est présent
                guilds = [guild] + [g for g in self.bot.guilds if g.id != guild.id]
                pages = self._build_pages(guilds)

                if not pages:
                    await safe_send(channel, "❌ Aucun emoji animé trouvé sur les serveurs.")
                    return

                view = EmojiPaginator(pages)
                await safe_send(channel, embed=pages[0], view=view)

        except Exception as e:
            print(f"[ERREUR affichage emojis] {e}")
            await safe_send(channel, "❌ Une erreur est survenue lors de l'affichage des emojis.")

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(
        name="emoji",
        aliases=["e"],
        help="😄 Affiche un ou plusieurs emojis du serveur.",
        description="Affiche les emojis demandés ou tous les emojis animés de tous les serveurs si aucun argument."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def prefix_emoji(self, ctx: commands.Context, *emoji_names):
        """Affiche les emojis du serveur en fonction des arguments fournis."""
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass
        await self._display_emojis(ctx.channel, ctx.guild, emoji_names)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="emoji", description="Affiche un ou plusieurs emojis du serveur ou tous les animés des serveurs.")
    @app_commands.describe(emojis="Noms des emojis à afficher, séparés par des espaces (optionnel)")
    async def slash_emoji(self, interaction: discord.Interaction, *, emojis: str = ""):
        """Commande slash qui affiche des emojis du serveur ou de tous les serveurs."""
        await interaction.response.defer()
        emoji_names = tuple(emojis.split()) if emojis else ()
        await self._display_emojis(interaction.channel, interaction.guild, emoji_names)
        try:
            await interaction.delete_original_response()
        except Exception:
            pass

    @slash_emoji.autocomplete("emojis")
    async def autocomplete_emojis(self, interaction: discord.Interaction, current: str):
        """Auto-complétion qui propose les noms d'emojis du serveur."""
        suggestions = [e.name for e in interaction.guild.emojis if e.available]
        return [app_commands.Choice(name=s, value=s) for s in suggestions if current.lower() in s.lower()][:25]

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = EmojiCommand(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Général"
    await bot.add_cog(cog)
