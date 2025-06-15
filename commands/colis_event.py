# ──────────────────────────────────────────────────────────────
# 📁 COG : GESTION DES RÉACTIONS AUX COLIS
# ──────────────────────────────────────────────────────────────
import discord
import random
from discord.ext import commands
from datetime import datetime, timedelta
from supabase_client import supabase  # Assure-toi que c’est bien importé

class ColisEvents(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) not in ["📦", "❌"]:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        user = guild.get_member(payload.user_id)
        if not user or user.bot:
            return

        # 🔍 Vérifie s'il y a un colis en cours
        colis_data = supabase.table("colis") \
            .select("*") \
            .eq("guild_id", str(payload.guild_id)) \
            .eq("ouvert", False) \
            .execute().data

        if not colis_data:
            return
        colis = colis_data[0]  # Un seul colis par serveur

        if int(payload.message_id) != int(colis["message_id"]):
            return

        if str(user.id) != colis["user_id"]:
            return  # ❌ Pas le bon destinataire

        channel = guild.get_channel(int(colis["channel_id"]))
        if not channel:
            return

        try:
            message = await channel.fetch_message(int(colis["message_id"]))
        except:
            return

        # 📦 OUVERTURE DU COLIS
        if str(payload.emoji) == "📦":
            await supabase.table("colis").update({"ouvert": True}).eq("id", colis["id"]).execute()

            embed = discord.Embed(
                title="🎁 Colis ouvert !",
                description=f"{user.mention} a ouvert le colis et a reçu :\n\n**{colis['content']}**",
                color=discord.Color.green()
            )
            await channel.send(embed=embed)
            try:
                await message.clear_reactions()
            except:
                pass

        # ❌ REFUS DU COLIS
        elif str(payload.emoji) == "❌":
            members = [
                m for m in guild.members if not m.bot and str(m.id) != colis["user_id"]
            ]
            if not members:
                await user.send("❌ Personne d'autre ne peut recevoir le colis.")
                return

            new_target = random.choice(members)
            await supabase.table("colis").update({
                "user_id": str(new_target.id),
                "expire_at": (datetime.utcnow() + timedelta(days=2)).isoformat()
            }).eq("id", colis["id"]).execute()

            await channel.send(f"📦 {user.mention} a refusé le colis. Il est maintenant entre les mains de {new_target.mention} !")
            try:
                await message.clear_reactions()
                await message.add_reaction("📦")
                await message.add_reaction("❌")
            except:
                pass

# 🔌 SETUP
async def setup(bot: commands.Bot):
    await bot.add_cog(ColisEvents(bot))
    print("✅ Cog chargé : ColisEvents (gestion des réactions)")
