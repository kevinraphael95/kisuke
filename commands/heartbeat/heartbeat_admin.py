# ────────────────────────────────────────────────────────────────────────────────
# 📌 heartbeat_admin.py — Commande !heartbeat <pause|resume|status|set|unset>
# Objectif : Gérer tout le heartbeat via une seule commande
# Catégorie : Heartbeat
# Accès : Modérateur (permission admin requise)
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands

class HeartbeatAdmin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.supabase = bot.supabase

    @commands.command(
        name="heartbeat",
        aliases=["hb"],
        help="Commande admin pour gérer le heartbeat : pause, resume, status, set, unset.",
        description="Gère le heartbeat automatique (pause, relance, statut, salon)."
    )
    @commands.has_permissions(administrator=True)
    async def heartbeat(self, ctx: commands.Context, action: str = None, channel: discord.TextChannel = None):
        try:
            if action is None:
                await ctx.send("❓ Utilisation : `!heartbeat pause|resume|status|set <#salon>|unset`")
                return

            action = action.lower()

            # Pause
            if action in ["pause", "p"]:
                self.supabase.table("bot_settings").upsert({
                    "key": "heartbeat_paused",
                    "value": "true"
                }).execute()
                await ctx.send("⏸️ Heartbeat mis en pause.")

            # Resume
            elif action in ["resume", "r"]:
                self.supabase.table("bot_settings").upsert({
                    "key": "heartbeat_paused",
                    "value": "false"
                }).execute()
                await ctx.send("▶️ Heartbeat relancé.")

            # Status
            elif action in ["status", "stat", "s"]:
                res = self.supabase.table("bot_settings").select("value").eq("key", "heartbeat_paused").execute()
                paused = res.data and res.data[0]["value"].lower() == "true"
                if paused:
                    await ctx.send("🔴 Le heartbeat est **en pause**.")
                else:
                    await ctx.send("🟢 Le heartbeat est **actif**.")

            # Set salon
            elif action == "set":
                if channel is None:
                    await ctx.send("❌ Tu dois mentionner un salon. Exemple : `!heartbeat set #général`")
                    return
                self.supabase.table("bot_settings").upsert({
                    "key": "heartbeat_channel_id",
                    "value": str(channel.id)
                }).execute()
                # Mise à jour dans le cog task si présent
                heartbeat_cog = self.bot.get_cog("HeartbeatTask")
                if heartbeat_cog:
                    heartbeat_cog.heartbeat_channel_id = channel.id
                await ctx.send(f"✅ Salon heartbeat défini : {channel.mention}")

            # Unset salon
            elif action == "unset":
                self.supabase.table("bot_settings").upsert({
                    "key": "heartbeat_channel_id",
                    "value": ""
                }).execute()
                heartbeat_cog = self.bot.get_cog("HeartbeatTask")
                if heartbeat_cog:
                    heartbeat_cog.heartbeat_channel_id = None
                await ctx.send("🗑️ Salon heartbeat supprimé.")

            else:
                await ctx.send("❌ Action inconnue. Utilise `pause`, `resume`, `status`, `set`, ou `unset`.")

        except Exception as e:
            print(f"[heartbeat:{action}] Erreur : {e}")
            await ctx.send("❌ Une erreur est survenue lors de l'action heartbeat.")

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
