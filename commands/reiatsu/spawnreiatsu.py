import discord
import asyncio
from datetime import datetime
from discord.ext import commands
from supabase_client import supabase

class SpawnReiatsuCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="spawnreiatsu",
        aliases=["spawnrts"],
        help="Force le spawn d’un Reiatsu dans le salon configuré. (Admin uniquement)"
    )
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def spawnreiatsu(self, ctx):
        guild_id = str(ctx.guild.id)

        # 📦 Cherche la config du salon
        config = supabase.table("reiatsu_config").select("channel_id").eq("guild_id", guild_id).execute()
        if not config.data:
            await ctx.send("❌ Aucun salon Reiatsu n’a été configuré. Utilise `!setreiatsu`.")
            return

        channel_id = int(config.data[0]["channel_id"])
        channel = self.bot.get_channel(channel_id)

        if not channel:
            await ctx.send("⚠️ Le salon configuré est introuvable.")
            return

        # 💠 Envoi du message de spawn
        embed = discord.Embed(
            title="💠 Un Reiatsu sauvage apparaît !",
            description="Cliquez sur la réaction 💠 pour l'absorber.",
            color=discord.Color.purple()
        )
        message = await channel.send(embed=embed)
        await message.add_reaction("💠")

        # 🔐 Enregistre l’état dans la DB
        supabase.table("reiatsu_config").update({
            "en_attente": True,
            "spawn_message_id": str(message.id),
            "last_spawn_at": datetime.utcnow().isoformat()
        }).eq("guild_id", guild_id).execute()

        def check(reaction, user):
            return (
                reaction.message.id == message.id
                and str(reaction.emoji) == "💠"
                and not user.bot
            )

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=10800.0, check=check)

            user_id = str(user.id)
            data = supabase.table("reiatsu").select("points").eq("user_id", user_id).execute()

            if data.data:
                current = data.data[0]["points"]
                supabase.table("reiatsu").update({"points": current + 1}).eq("user_id", user_id).execute()
            else:
                supabase.table("reiatsu").insert({
                    "user_id": user_id,
                    "username": user.name,
                    "points": 1
                }).execute()

            await channel.send(f"{user.mention} a absorbé le Reiatsu et gagné **+1** point !")

        except asyncio.TimeoutError:
            await channel.send("⏳ Le Reiatsu s’est dissipé dans l’air... personne ne l’a absorbé.")

        # 🔄 Déverrouille le spawn
        supabase.table("reiatsu_config").update({
            "en_attente": False,
            "spawn_message_id": None
        }).eq("guild_id", guild_id).execute()

# ✅ Chargement automatique avec catégorie
async def setup(bot):
    cog = SpawnReiatsuCommand(bot)  # ✅ Classe correctement instanciée
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
