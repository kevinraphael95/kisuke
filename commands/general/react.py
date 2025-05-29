# ──────────────────────────────────────────────────────────────
# 📁 FICHIER : commands/general/react.py
# ──────────────────────────────────────────────────────────────
# 🧾 COMMANDE : !react :emoji:
# 🎯 OBJET : Réagit à un message avec un emoji animé et le retire après 3 min
# 📂 CATÉGORIE : Général
# 🕒 COOLDOWN : 3 secondes par utilisateur
# ──────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
import asyncio

# ──────────────────────────────────────────────────────────────
# 🔧 COG : ReactCommand
# ──────────────────────────────────────────────────────────────
class ReactCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot  # 🔌 Stocke la référence au bot

    # ──────────────────────────────────────────────────────────
    # 💬 COMMANDE : !react :nom_emoji: (alias : !r)
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="react",
        aliases=["r"],  # 🏷️ Alias : !r
        help="Réagit à un message avec un emoji animé, puis le retire après 3 minutes."
    )
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🧊 Anti-spam (3s)
    async def react(self, ctx: commands.Context, emoji_name: str):
        # 🔇 Supprime la commande du salon pour garder ça clean
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

        # 🔍 Nettoie le nom de l’emoji donné
        name = emoji_name.strip(":").lower()

        # 🧠 Cherche l’emoji animé dans les emojis du serveur
        emoji = next(
            (e for e in ctx.guild.emojis if e.animated and e.name.lower() == name),
            None
        )
        if not emoji:
            await ctx.send(f"❌ Emoji animé `:{name}:` introuvable sur ce serveur.", delete_after=5)
            return

        target_message = None

        # 📌 Si c’est une réponse à un message
        if ctx.message.reference:
            try:
                target_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except discord.NotFound:
                await ctx.send("❌ Message référencé introuvable.", delete_after=5)
                return
        else:
            # 🧭 Sinon, cherche le dernier message juste avant celui-ci
            async for msg in ctx.channel.history(limit=20, before=ctx.message.created_at):
                if msg.id != ctx.message.id:
                    target_message = msg
                    break

        # ❗ Vérifie qu’on a bien un message cible
        if not target_message or target_message.id == ctx.message.id:
            await ctx.send("❌ Aucun message valide à réagir.", delete_after=5)
            return

        try:
            # ✅ Ajoute la réaction
            await target_message.add_reaction(emoji)
            print(f"✅ Réaction {emoji} ajoutée au message {target_message.id}")

            # ⏳ Attente de 3 minutes
            await asyncio.sleep(180)

            # 🔁 Supprime la réaction du bot après délai
            await target_message.remove_reaction(emoji, ctx.guild.me)
            print(f"🔁 Réaction {emoji} retirée du message {target_message.id}")

        except Exception as e:
            print(f"⚠️ Erreur de réaction : {e}")

    # 🏷️ Ajoute la commande à la bonne catégorie pour les commandes groupées
    def cog_load(self):
        self.react.category = "Général"

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP POUR CHARGEMENT AUTO DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(ReactCommand(bot))
    print("✅ Cog chargé : ReactCommand (catégorie = Général)")
