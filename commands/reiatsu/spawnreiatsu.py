# ──────────────────────────────────────────────────────────────
# 📁 REIATSU - COMMANDE DE SPAWN FORCÉ
# ──────────────────────────────────────────────────────────────

import discord
import asyncio
from datetime import datetime
from discord.ext import commands
from supabase_client import supabase

# ──────────────────────────────────────────────────────────────
# 🔧 COG : SpawnReiatsuCommand
# ──────────────────────────────────────────────────────────────
class SpawnReiatsuCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ──────────────────────────────────────────────────────────
    # 💠 COMMANDE : spawnreiatsu
    # ──────────────────────────────────────────────────────────
    @commands.command(
        name="spawnreiatsu",
        aliases=["spawnrts"],
        help="Force le spawn d’un Reiatsu dans le salon configuré. (Admin uniquement)"
    )
    @commands.has_permissions(administrator=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)  # 🕒 3 secondes de cooldown
    async def spawnreiatsu(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)

        # 📦 Récupère la configuration du salon Reiatsu
        config = supabase.table("reiatsu_config").select("channel_id").eq("guild_id", guild_id).execute()
        if not config.data:
            await ctx.send("❌ Aucun salon Reiatsu n’a été configuré. Utilise `!setreiatsu`.")
            return

        channel_id = int(config.data[0]["channel_id"])
        channel = self.bot.get_channel(channel_id)

        if not channel:
            await ctx.send("⚠️ Le salon configuré est introuvable.")
            return

        # ✨ Envoie le message de spawn avec réaction
        embed = discord.Embed(
            title="💠 Un Reiatsu sauvage apparaît !",
            description="Cliquez sur la réaction 💠 pour l'absorber.",
            color=discord.Color.purple()
        )
        message = await channel.send(embed=embed)
        await message.add_reaction("💠")

        # 💾 Mise à jour de l’état dans la base
        supabase.table("reiatsu_config").update({
            "en_attente": True,
            "spawn_message_id": str(message.id),
            "last_spawn_at": datetime.utcnow().isoformat()
        }).eq("guild_id", guild_id).execute()

        # ✅ Attend qu’un utilisateur clique sur 💠
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

            await channel.send(f"💠 {user.mention} a absorbé le Reiatsu et gagné **+1** point !")

        except asyncio.TimeoutError:
            await channel.send("⏳ Le Reiatsu s’est dissipé dans l’air... personne ne l’a absorbé.")

        # 🔄 Réinitialisation de l’état
        supabase.table("reiatsu_config").update({
            "en_attente": False,
            "spawn_message_id": None
        }).eq("guild_id", guild_id).execute()

# ──────────────────────────────────────────────────────────────
# 🔌 SETUP AUTOMATIQUE DU COG
# ──────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = SpawnReiatsuCommand(bot)
    for command in cog.get_commands():
        command.category = "Reiatsu"
    await bot.add_cog(cog)
    print("✅ Cog chargé : SpawnReiatsuCommand (Spawn manuel)")
