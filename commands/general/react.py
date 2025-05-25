import discord
from discord.ext import commands
import asyncio

class ReactCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="react", aliases=["r"], help="Réagit à un message avec un emoji animé, puis le retire après 3 minutes.")
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 Cooldown de 3s par utilisateur
    async def react(self, ctx, emoji_name: str):
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

        name = emoji_name.strip(":").lower()

        # 🔎 Recherche l’emoji animé dans le serveur
        emoji = next((e for e in ctx.guild.emojis if e.animated and e.name.lower() == name), None)
        if not emoji:
            await ctx.send(f"❌ Emoji animé `:{name}:` introuvable sur ce serveur.", delete_after=5)
            return

        target_message = None

        # 🎯 Si réponse à un message
        if ctx.message.reference:
            try:
                target_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            except discord.NotFound:
                await ctx.send("❌ Message référencé introuvable.", delete_after=5)
                return
        else:
            # 🔄 Sinon, cherche le dernier message avant cette commande
            async for msg in ctx.channel.history(limit=20, before=ctx.message.created_at):
                if msg.id != ctx.message.id:
                    target_message = msg
                    break

        if not target_message or target_message.id == ctx.message.id:
            await ctx.send("❌ Aucun message valide à réagir.", delete_after=5)
            return

        try:
            await target_message.add_reaction(emoji)
            print(f"✅ Réaction {emoji} ajoutée au message {target_message.id}")
            await asyncio.sleep(180)  # ⏳ Attente de 3 minutes
            await target_message.remove_reaction(emoji, ctx.guild.me)
            print(f"🔁 Réaction {emoji} retirée du message {target_message.id}")
        except Exception as e:
            print(f"⚠️ Erreur de réaction : {e}")

# Chargement automatique du module
async def setup(bot):
    await bot.add_cog(ReactCommand(bot))
