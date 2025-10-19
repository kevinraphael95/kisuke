# ────────────────────────────────────────────────────────────────────────────────
# 📌 entrainement_cerebral.py — Commande /cerebral et !cerebral
# Objectif : Lancer 5 mini-jeux aléatoires style Professeur Kawashima avec score arcade
# Catégorie : Autre
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
import random
import time
import inspect
import asyncio
from utils import kawashima_games
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# Table
# ────────────────────────────────────────────────────────────────────────────────
TABLE_NAME = "kawashima_scores"

# ────────────────────────────────────────────────────────────────────────────────
# Commande
# ────────────────────────────────────────────────────────────────────────────────
class EntrainementCerebral(commands.Cog):
    """Mode arcade — Entraînement cérébral avec classement global."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.minijeux = []
        for name, func in inspect.getmembers(kawashima_games, inspect.iscoroutinefunction):
            if not name.startswith("_"):
                emoji = getattr(func, "emoji", "🎮")
                titre = getattr(func, "title", func.__name__.replace("_", " ").title())
                self.minijeux.append((f"{emoji} {titre}", func))

    # ─────────── Commande texte ───────────
    @commands.command(name="entrainementcerebral", aliases=["ec", "kawashima", "k"], help="Lance le mode arcade ou affiche le top 10.")
    async def cerebral_cmd(self, ctx: commands.Context, arg: str = ""):
        if arg.lower() == "top":
            await self.show_leaderboard(ctx)
        elif arg.lower() in ["m", "multi"]:
            await self.run_arcade(ctx, multiplayer=True)
        else:
            await self.run_arcade(ctx)

    # ─────────── Commande slash ───────────
    @app_commands.command(name="cerebral", description="Mode arcade Entraînement cérébral ou Top 10.")
    async def cerebral_slash(self, interaction: discord.Interaction, arg: str = ""):
        if arg.lower() == "top":
            await self.show_leaderboard(interaction)
        elif arg.lower() in ["m", "multi"]:
            await self.run_arcade(interaction, multiplayer=True)
        else:
            await self.run_arcade(interaction)

    # ─────────── Lancement du mode arcade ───────────
    async def run_arcade(self, ctx_or_interaction, multiplayer=False):
        # Gestion du contexte
        if isinstance(ctx_or_interaction, discord.Interaction):
            send = ctx_or_interaction.channel.send
            users = [ctx_or_interaction.user]
        else:
            send = ctx_or_interaction.send
            users = [ctx_or_interaction.author]

        total_score = {}
        results = {}

        # ─────────── Message d'introduction et bouton "Je suis prêt" ───────────
        start_embed = discord.Embed(
            title="🧠 Entraînement cérébral — Mode Arcade",
            description=(
                "Bienvenue dans le **Mode Arcade Entraînement cérébral** ! 🧩\n\n"
                "🧠 Tu vas affronter **5 mini-jeux** choisis au hasard.\n"
                "Réponds **vite et bien** pour marquer un maximum de points !\n\n"
                f"{'🔹 Mode Multijoueur : au moins 2 joueurs requis.' if multiplayer else ''}\n"
                "Appuie sur le bouton ci-dessous quand tu es prêt à commencer."
            ),
            color=discord.Color.blurple(),
        )

        ready_users = []

        class ReadyButton(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)
                self.ready_event = asyncio.Event()

            @discord.ui.button(label="🟢 Je suis prêt !", style=discord.ButtonStyle.success)
            async def ready(self, interaction: discord.Interaction, button: discord.ui.Button):
                if multiplayer:
                    if interaction.user in ready_users:
                        return await interaction.response.send_message("✅ Tu es déjà prêt !", ephemeral=True)
                    ready_users.append(interaction.user)
                    await interaction.response.send_message(f"✅ {interaction.user.name} est prêt !", ephemeral=True)
                    if len(ready_users) >= 2:
                        button.disabled = True
                        button.label = "✅ On y va !"
                        self.ready_event.set()
                else:
                    if interaction.user != users[0]:
                        return await interaction.response.send_message("🚫 Ce n’est pas ton entraînement.", ephemeral=True)
                    button.disabled = True
                    button.label = "✅ C’est parti !"
                    self.ready_event.set()

            async def on_timeout(self):
                for child in self.children:
                    child.disabled = True
                    child.label = "⏰ Temps écoulé"
                self.ready_event.set()

        view = ReadyButton()
        msg_start = await send(embed=start_embed, view=view)
        await view.ready_event.wait()

        if multiplayer and len(ready_users) < 2:
            timeout_embed = discord.Embed(
                title="⏰ Temps écoulé",
                description="Au moins 2 joueurs n'ont pas cliqué à temps. Relancez la commande !",
                color=discord.Color.red()
            )
            return await msg_start.edit(embed=timeout_embed, view=None)
        if not multiplayer and not view.ready_event.is_set():
            timeout_embed = discord.Embed(
                title="⏰ Temps écoulé",
                description="Tu n’as pas cliqué à temps. Relance la commande pour rejouer !",
                color=discord.Color.red()
            )
            return await msg_start.edit(embed=timeout_embed, view=None)

        # ─────────── Sélection de 5 mini-jeux ───────────
        random.shuffle(self.minijeux)
        selected_games = self.minijeux[:5]

        active_players = ready_users if multiplayer else users

        # ─────────── Boucle des mini-jeux ───────────
        for index, (name, game) in enumerate(selected_games, start=1):
            for player in active_players:
                get_user_id = lambda p=player: p.id
                game_embed = discord.Embed(
                    title=f"🧩 Mini-jeu {index} — {name}",
                    description=f"{player.mention}, réponds rapidement !",
                    color=discord.Color.blurple()
                )
                msg_game = await send(embed=game_embed)
                start = time.time()
                success = await game(msg_game, game_embed, get_user_id, self.bot)
                elapsed = round(time.time() - start, 2)
                score = (1000 + max(0, 500 - int(elapsed * 25))) if success else 0
                total_score[player.id] = total_score.get(player.id, 0) + score
                results.setdefault(player.id, []).append((index, name, success, elapsed, score))
                result_embed = discord.Embed(
                    title=f"🎯 Résultat — {name} ({player.name})",
                    description=(
                        f"{'✅ Réussi' if success else '❌ Raté'}\n"
                        f"⏱️ Temps : `{elapsed}s`\n"
                        f"🏅 Score : `{score}` pts"
                    ),
                    color=discord.Color.green() if success else discord.Color.red()
                )
                await send(embed=result_embed)
                await asyncio.sleep(1.5)

        # ─────────── Embed final par joueur ───────────
        for player in active_players:
            player_results = results[player.id]
            results_text = "\n".join(
                f"**Jeu {i}** {'✅' if s else '❌'} {name}{f' — {t}s' if s else ''}"
                for i, name, s, t, _ in player_results
            )
            total = total_score[player.id]

            if total >= 5000:
                rank = "🧠 Génie cérébral"
            elif total >= 3500:
                rank = "🤓 Bonne forme mentale"
            elif total >= 2000:
                rank = "🙂 Correct"
            else:
                rank = "😴 En veille..."

            final_embed = discord.Embed(
                title=f"🏁 Résultats — {player.name}",
                description=(
                    f"**Résultats des 5 jeux :**\n{results_text}\n\n"
                    f"**Score total :** `{total:,}` pts\n"
                    f"**Niveau cérébral :** {rank}"
                ),
                color=discord.Color.gold()
            )
            await send(embed=final_embed)

    # ─────────── Affichage du classement ───────────
    async def show_leaderboard(self, ctx_or_interaction):
        embed = discord.Embed(
            title="🏆 Entraînement cérébral — Top 10",
            description="Voici le classement global des meilleurs scores !",
            color=discord.Color.gold()
        )

        try:
            leaderboard = (
                supabase.table(TABLE_NAME)
                .select("username, score")
                .order("score", desc=True)
                .limit(10)
                .execute()
            )
            entries = leaderboard.data if leaderboard and leaderboard.data else []
            top_text = "\n".join(
                f"**{i+1}.** {entry['username']} — `{entry['score']:,}` pts"
                for i, entry in enumerate(entries)
            ) or "*Aucun score enregistré pour le moment*"
        except Exception as e:
            top_text = f"⚠️ Erreur récupération classement : {e}"

        embed.add_field(name="Top 10", value=top_text, inline=False)

        if isinstance(ctx_or_interaction, discord.Interaction):
            await ctx_or_interaction.response.send_message(embed=embed)
        else:
            await ctx_or_interaction.send(embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = EntrainementCerebral(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
