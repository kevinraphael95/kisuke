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

        # ──────────────── Limite de longueur du prompt ────────────────
        if len(prompt) > 90:
            await self._embed_send(
                channel,
                "⚠️ **Trop long !**",
                f"Ton message dépasse la limite de **90 caractères**.\n"
                f"({len(prompt)} actuellement)"
            )
            return

        try:
            # Appel au modèle NVIDIA GPT-OSS (cloud)
            response = await asyncio.to_thread(get_simple_response, prompt)

            # ──────────────── Limite de longueur de la réponse ────────────────
            if not response:
                response = "⚠️ Réponse vide ou erreur du modèle."
            elif len(response) > 250:
                response = response[:250].rstrip() + "…"

        except Exception as e:
            print(f"[Erreur GPT Commande] {e}")
            await self._embed_send(channel, "⚠️ **Erreur :**", "Impossible de contacter le modèle pour le moment.")
            return

        await self._embed_send(channel, f"💬 **Réponse à {user.display_name} :**", response)

    # ────────────────────────────────────────────────────────────────────────────
    # 🪶 Envoi propre en embed
    # ────────────────────────────────────────────────────────────────────────────
    async def _embed_send(self, channel: discord.TextChannel, title: str, description: str):
        if not description:
            description = "⚠️ Aucune donnée à afficher."
        elif len(description) > 4000:
            description = description[:4000] + "\n\n…(contenu tronqué)"

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
            command.category = "Fun&Random"
    await bot.add_cog(cog)
