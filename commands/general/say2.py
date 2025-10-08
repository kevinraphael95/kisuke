# commands/general/say_emoji.py

import discord
from discord import app_commands
from discord.ext import commands
from utils.discord_utils import safe_send, safe_delete, safe_respond
from utils.emoji_utils import run_emoji_code

code = """
🏗️ 💭(⚡c.Cog):
    🐍 🐝(📝, 🛠️):
        📝.🛠️ = 🛠️

    # ────────────── Fonction d'envoi ──────────────
    🐍 📢(📝, 📡, 💬: str, 🧃=❎):
        🟰 not 💬: 🔙
        🟰 len(💬) > 🔢:
            💬 = 💬[:🔢 - 3] + "..."
        🟰 🧃:
            🧊 = 🐉.🧊(description=💬, color=🐉.🎨.blurple())
            ⚡️ 🛡️(📡, embed=🧊, allowed_mentions=🐉.👀.none())
        ❌:
            ⚡️ 🛡️(📡, 💬, allowed_mentions=🐉.👀.none())

    # ────────────── Commande Slash ──────────────
    ⚡(
        name="say_emoji",
        description=💬🔁
    )
    🐍 slash_say(📝, interaction: 🐉.Interaction, 💬: str, 🧃=❎):
        🌀:
            ⚡️ interaction.response.defer()
            ⚡️ 📝.📢(interaction.channel, 💬, 🧃)
            ⚡️ 📝💬(interaction, 💌, ephemeral=True)
        🌪️ 💥 🖨️(e):
            🖨️(e)
            ⚡️ 📝💬(interaction, 🔥, ephemeral=True)

    # ────────────── Commande Préfix ──────────────
    🧩
    🐍 prefix_say(📝, ctx: ⚡c.Context, *, 💬: str):
        🌀:
            ⚡️ 📝.📢(ctx.channel, 💬)
        🌪️ 💥 🖨️(e):
            🖨️(e)
            ⚡️ 🛡️(ctx.channel, 🔥)
        💨:
            ⚡️ 🗑️(ctx.message)

🐍 setup(🛠️):
    cog = 💭(🛠️)
    ⚡️ 🛠️.add_cog(cog)
"""

run_emoji_code(code, globals())
