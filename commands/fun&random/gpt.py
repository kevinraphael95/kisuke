# ────────────────────────────────────────────────────────────────────────────────
# 📌 gpt.py — Commande !!gpt : Chat libre avec GPT-OSS (Cloud NVIDIA)
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
import asyncio
from utils.gpt_oss_client import get_simple_response

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 COG PRINCIPAL
# ────────────────────────────────────────────────────────────────────────────────
class GPTChat(commands.Cog):
    """Commande !!gpt — conversation libre avec le modèle GPT-OSS (Cloud NVIDIA)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 💬 Commande principale : !!gpt <message>
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="gpt")
    @commands.cooldown(1, 4.0, commands.BucketType.user)
    async def gpt_command(self, ctx: commands.Context, *, prompt: str = None):
        user = ctx.author
        channel = ctx.channel

        if not prompt:
            await self._embed_send(
                channel,
                "💭 **Utilisation :**",
                "Tape simplement `!!gpt <ton message>` pour discuter avec le modèle.\n"
                "Exemple : `!!gpt explique-moi le Bankai d’Ichigo`"
            )
            return

        try:
            # Appel au modèle NVIDIA GPT-OSS (cloud)
            response = await asyncio.to_thread(get_simple_response, prompt)
        except Exception as e:
            print(f"[Erreur GPT Commande] {e}")
            await self._embed_send(channel, "⚠️ **Erreur :**", "Impossible de contacter le modèle pour le moment.")
            return

        await self._embed_send(channel, f"💬 **Réponse à {user.display_name} :**", response)

    # ────────────────────────────────────────────────────────────────────────────
    # 🪶 Envoi propre en embed
    # ────────────────────────────────────────────────────────────────────────────
    async def _embed_send(self, channel: discord.TextChannel, title: str, description: str):
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blurple()
        )
        embed.set_footer(text="GPT-OSS NVIDIA • Cloud")
        await channel.send(embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 SETUP DU COG
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = GPTChat(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Utilitaires"
    await bot.add_cog(cog)
