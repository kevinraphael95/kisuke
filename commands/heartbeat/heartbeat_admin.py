# ────────────────────────────────────────────────────────────────────────────────
# 📌 heartbeat_admin.py — Commandes pour activer ou désactiver le heartbeat
# Objectif : Donner aux admins un moyen de contrôler le heartbeat dynamiquement
# Catégorie : Heartbeat
# Accès : Modérateur (permission admin requise)
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands

class HeartbeatAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.supabase = bot.supabase

    @commands.command(name="heartbeatpause", aliases=["pausehb", "hbpause"], help="Pause le heartbeat automatique.", description="Désactive temporairement le heartbeat.")
    @commands.has_permissions(administrator=True)
    async def pauseheartbeat(self, ctx: commands.Context):
        try:
            self.supabase.table("bot_settings").upsert({
                "key": "heartbeat_paused",
                "value": "true"
            }).execute()
            await ctx.send("⏸️ Heartbeat mis en pause.")
        except Exception as e:
            print(f"[pauseheartbeat] Erreur : {e}")
            await ctx.send("❌ Erreur en mettant en pause le heartbeat.")

    @commands.command(name="heartbeatresume", aliases=["hbresume"], help="Relance le heartbeat automatique.", description="Réactive le heartbeat.")
    @commands.has_permissions(administrator=True)
    async def resumeheartbeat(self, ctx: commands.Context):
        try:
            self.supabase.table("bot_settings").upsert({
                "key": "heartbeat_paused",
                "value": "false"
            }).execute()
            await ctx.send("▶️ Heartbeat relancé.")
        except Exception as e:
            print(f"[resumeheartbeat] Erreur : {e}")
            await ctx.send("❌ Erreur en relançant le heartbeat.")

    @commands.command(name="heartbeatstatus", aliases=["hbstatus", "hbstat"], help="Affiche l'état actuel du heartbeat.", description="Vérifie si le heartbeat est actif ou en pause.")
    @commands.has_permissions(administrator=True)
    async def heartbeatstatus(self, ctx: commands.Context):
        try:
            res = self.supabase.table("bot_settings").select("value").eq("key", "heartbeat_paused").execute()
            paused = False

            if res.data and res.data[0]["value"].lower() == "true":
                paused = True

            if paused:
                await ctx.send("🔴 Le heartbeat est **en pause**.")
            else:
                await ctx.send("🟢 Le heartbeat est **actif**.")
        except Exception as e:
            print(f"[heartbeatstatus] Erreur : {e}")
            await ctx.send("❌ Erreur en consultant le statut du heartbeat.")




# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HeartbeatAdmin(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Heartbeat"
    await bot.add_cog(cog)
    print("✅ Cog chargé : HeartbeatAdmin (catégorie = Heartbeat)")
