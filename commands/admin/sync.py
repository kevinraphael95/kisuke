# ────────────────────────────────────────────────────────────────────────────────
# 📌 sync.py — Commande pour synchroniser les commandes slash
# Catégorie : Admin
# Accès : Owner uniquement
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands

class Sync(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="sync")
    @commands.is_owner()  # Seul le propriétaire du bot peut l'utiliser
    async def sync(self, ctx: commands.Context):
        """Synchronise les commandes slash avec Discord"""
        try:
            synced = await ctx.bot.tree.sync()
            await ctx.send(f"✅ **{len(synced)} commandes slash synchronisées avec Discord !**")
        except Exception as e:
            await ctx.send(f"❌ **Erreur lors de la synchronisation :** `{e}`")

async def setup(bot: commands.Bot):
    await bot.add_cog(Sync(bot))
