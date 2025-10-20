# ────────────────────────────────────────────────────────────────────────────────
# 📌 buckshot.py — Commande /buckshot et !buckshot (Buckshot Roulette)
# Objectif : Partie 1v1 identique au jeu Buckshot Roulette — solo contre le bot ou défi avec mention
# Catégorie : Fun / Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# Remarques : Utilise Supabase + utils.discord_utils.safe_send / safe_edit / safe_followup
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
import asyncio
import random
import json
import time

from utils.discord_utils import safe_send, safe_edit, safe_followup
from utils.buckshot_utils import make_barillet, apply_item

from supabase import create_client, Client
import os

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Buckshot(commands.Cog):
    """
    Commande /buckshot et !buckshot — Jouer au Buckshot Roulette (1v1).
    Usage :
    - !buckshot -> solo contre le bot
    - !buckshot @membre -> défier un joueur (il doit accepter)
    Mécaniques :
    - Barillet 6 chambres, bullets aléatoires (1-5 par manche)
    - Objets : cigarette, bière, loupe, menottes, scie, adrenaline
    - Tour par tour, affichage embed + boutons d'action
    - Une seule session par serveur à la fois
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_sessions = set()  # guild ids avec partie active
        self.CHAMBRE_COUNT = 6
        self.MIN_BULLETS = 1
        self.MAX_BULLETS = 5
        self.START_HP = 3

        # Supabase client
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

        # items JSON
        with open("data/buckshot_items.json", "r") as f:
            self.ITEMS = json.load(f)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="buckshot")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_buckshot(self, ctx: commands.Context, target: Optional[discord.Member] = None):
        await self._start_request(ctx, target)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(
        name="buckshot",
        description="Joue au Buckshot Roulette (solo ou défie quelqu'un)."
    )
    @app_commands.describe(target="Mentionnez un joueur pour le défier (optionnel).")
    async def slash_buckshot(self, interaction: discord.Interaction, target: Optional[discord.Member] = None):
        await interaction.response.defer()
        await self._start_request(interaction, target)
    
    # ────────────────────────────────────────────────────────────────────────────
    # ▶️ Démarrage / demande d'acceptation / solo
    # ────────────────────────────────────────────────────────────────────────────
    async def _start_request(self, ctx_or_interaction, target: Optional[discord.Member]):
        guild = getattr(ctx_or_interaction, "guild", None)
        guild_id = guild.id if guild else None

        if guild_id in self.active_sessions:
            return await self._respond(ctx_or_interaction, "⚠️ Une partie est déjà en cours sur ce serveur.", ephemeral=True)

        author = ctx_or_interaction.author if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.user

        if target:
            desc = f"{author.mention} défie {target.mention} au **Buckshot Roulette**.\n{target.mention}, acceptez-vous ?"
            title = "🎯 Défi Buckshot Roulette"
        else:
            desc = f"{author.mention} lance une partie solo contre le bot.\nClique sur **Jouer** pour démarrer."
            title = "🎯 Buckshot Roulette — Solo"

        embed = discord.Embed(title=title, description=desc, color=discord.Color.blurple())

        # ────────── View d’invitation ──────────
        class InviteView(discord.ui.View):
            def __init__(self, timeout=30):
                super().__init__(timeout=timeout)
                self.result = None
                self.msg = None

            @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success)
            async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not target:
                    return await interaction.response.send_message("Ce bouton n'est pas applicable.", ephemeral=True)
                if interaction.user.id != target.id:
                    return await interaction.response.send_message("🔒 Seul le défié peut accepter.", ephemeral=True)
                button.disabled = True
                self.result = "accept"
                await interaction.response.edit_message(view=self)
                self.stop()

            @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
            async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not target:
                    return await interaction.response.send_message("Ce bouton n'est pas applicable.", ephemeral=True)
                    return
                if interaction.user.id != target.id:
                    return await interaction.response.send_message("🔒 Seul le défié peut refuser.", ephemeral=True)
                self.result = "refuse"
                await interaction.response.edit_message(view=self)
                self.stop()

            @discord.ui.button(label="🟢 Jouer (solo)", style=discord.ButtonStyle.primary)
            async def solo(self, interaction: discord.Interaction, button: discord.ui.Button):
                if target:
                    return await interaction.response.send_message("🔒 Ce bouton est pour le solo uniquement.", ephemeral=True)
                if interaction.user.id != author.id:
                    return await interaction.response.send_message("🔒 Seul l'initiateur peut démarrer.", ephemeral=True)
                self.result = "solo"
                await interaction.response.edit_message(view=self)
                self.stop()

            @discord.ui.button(label="✖️ Annuler", style=discord.ButtonStyle.secondary)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                if (target and interaction.user.id not in (author.id, target.id)) or (not target and interaction.user.id != author.id):
                    return await interaction.response.send_message("🔒 Vous ne pouvez pas annuler cette demande.", ephemeral=True)
                self.result = "cancel"
                await interaction.response.edit_message(view=self)
                self.stop()

            async def on_timeout(self):
                self.result = "timeout"
                if self.msg:
                    await safe_edit(self.msg, embed=discord.Embed(
                        title="⏰ Temps écoulé",
                        description="La demande a expiré.",
                        color=discord.Color.red()
                    ), view=None)
                self.stop()

        view = InviteView(timeout=30)

        if isinstance(ctx_or_interaction, commands.Context):
            msg = await safe_send(ctx_or_interaction.channel, embed=embed, view=view)
        else:
            msg = await safe_followup(ctx_or_interaction, embed=embed, view=view)
        view.msg = msg

        await view.wait()
        res = view.result

        if res == "accept":
            players = [author, target]
            await safe_edit(msg, embed=discord.Embed(
                title="⚔️ Début du duel",
                description=f"{author.mention} vs {target.mention}\nPréparez-vous...",
                color=discord.Color.dark_teal()
            ), view=None)
            if guild_id:
                self.active_sessions.add(guild_id)
            await asyncio.sleep(1.2)
            await self._start_game(msg.channel if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.channel, players, msg, guild_id)
        elif res == "solo":
            players = [author, self.bot.user]
            await safe_edit(msg, embed=discord.Embed(
                title="🤖 Solo contre le bot",
                description=f"{author.mention} vs {self.bot.user.mention}\nPréparez-vous...",
                color=discord.Color.dark_teal()
            ), view=None)
            if guild_id:
                self.active_sessions.add(guild_id)
            await asyncio.sleep(1.2)
            await self._start_game(msg.channel if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.channel, players, msg, guild_id)
        else:
            content = "❌ Défi refusé." if res == "refuse" else "✖️ Défi annulé." if res == "cancel" else "⏰ Temps écoulé."
            await safe_edit(msg, embed=discord.Embed(title="Fin de la demande", description=content, color=discord.Color.red()), view=None)


    #sg
	async def _start_game(self, channel: discord.abc.Messageable, players: list, invite_msg: discord.Message, guild_id: Optional[int]):
		"""
		Lance la partie Buckshot Roulette (1v1). players = [joueur1, joueur2] (2e peut être bot).
		"""
		# Initialisation
		p1, p2 = players
		state = {
			"players": {
				p1.id: {"user": p1, "hp": self.START_HP, "items": [], "alive": True},
				p2.id: {"user": p2, "hp": self.START_HP, "items": [], "alive": True},
			},
			"current_player": p1.id,
			"turn": 0,
			"history": [],
			"winner": None,
			"menotte_until": None,
			"scie_flags": {},
			"adrenaline_flags": {}
		}

		ITEM_POOL = ["cigarette", "biere", "loupe", "menottes", "scie", "adrenaline"]
		for pid in state["players"]:
			n_items = random.choice([1, 1, 2])
			state["players"][pid]["items"] = random.sample(ITEM_POOL, k=n_items)

		# Fonction helper pour créer embed du tour
		async def make_game_embed(note: str = ""):
			lines = []
			for pid, pdata in state["players"].items():
				u = pdata["user"]
				hp = pdata["hp"]
				items = ", ".join(pdata["items"]) or "—"
				lines.append(f"**{u.display_name}** — ❤️ {hp} — 🧰 {items}")
			desc = ("\n".join(lines))
			if note:
				desc = note + "\n\n" + desc
			return discord.Embed(title="🎲 Buckshot Roulette", description=desc, color=discord.Color.dark_gold()).set_footer(text="Actions : Tirer / Passer / Utiliser un objet")

		# Barillet aléatoire
		def make_barillet():
			bullets = random.randint(self.MIN_BULLETS, self.MAX_BULLETS)
			arr = [True]*bullets + [False]*(self.CHAMBRE_COUNT - bullets)
			random.shuffle(arr)
			return arr

		# Appliquer effet d’un objet
		def apply_item_effect(player_id: int, item: str, state_local: dict, barillet: list):
			note = ""
			alter = False
			if item == "cigarette":
				state_local["players"][player_id]["hp"] = min(5, state_local["players"][player_id]["hp"] + 1)
				note = f"{state_local['players'][player_id]['user'].display_name} fume une cigarette et récupère ❤️1."
			elif item == "biere":
				if True in barillet:
					barillet[barillet.index(True)] = False
					note = f"{state_local['players'][player_id]['user'].display_name} boit une bière et retire une balle du barillet."
					alter = True
			elif item == "loupe":
				note = f"{state_local['players'][player_id]['user'].display_name} regarde avec une loupe."
				alter = "peek"
			elif item == "menottes":
				note = f"{state_local['players'][player_id]['user'].display_name} menotte l'adversaire (il perd son prochain tour)."
				alter = "menotte"
			elif item == "scie":
				note = f"{state_local['players'][player_id]['user'].display_name} prépare la scie (prochain tir inflige +1 dégât)."
				state_local["scie_flags"][player_id] = True
			elif item == "adrenaline":
				note = f"{state_local['players'][player_id]['user'].display_name} prend de l'adrénaline (action supplémentaire)."
				state_local["adrenaline_flags"][player_id] = True
			else:
				note = f"{state_local['players'][player_id]['user'].display_name} a tenté d'utiliser un objet inconnu."
			return note, alter

		last_embed = await make_game_embed("Début de la partie")
		game_msg = await safe_send(channel, embed=last_embed)
		finished = False

		while not finished:
			state["turn"] += 1
			cur_id = state["current_player"]
			cur_data = state["players"][cur_id]
			cur_user = cur_data["user"]
			opp_id = [k for k in state["players"] if k != cur_id][0]

			# Gestion menottes
			if state.get("menotte_until") == cur_id:
				note = f"🔒 {cur_user.display_name} est menotté et perd ce tour."
				state["menotte_until"] = None
				state["current_player"] = opp_id
				await safe_edit(game_msg, embed=await make_game_embed(note))
				await asyncio.sleep(1.2)
				continue

			# Barillet
			barillet = make_barillet()

			# View pour boutons actions
			class ActionView(discord.ui.View):
				def __init__(self, players_ids: list, timeout=40):
					super().__init__(timeout=timeout)
					self.players_ids = players_ids
					self.msg = None
					self.action = None
				def _is_current(self, interaction):
					return interaction.user.id == state["current_player"]

				@discord.ui.button(label="🔫 Tirer", style=discord.ButtonStyle.danger)
				async def shoot(self, interaction, button):
					if not self._is_current(interaction):
						return await interaction.response.send_message("🔒 Ce n'est pas ton tour.", ephemeral=True)
					self.action = ("shoot", None)
					await interaction.response.defer()
					self.stop()

				@discord.ui.button(label="⏭️ Passer", style=discord.ButtonStyle.secondary)
				async def passer(self, interaction, button):
					if not self._is_current(interaction):
						return await interaction.response.send_message("🔒 Ce n'est pas ton tour.", ephemeral=True)
					self.action = ("pass", None)
					await interaction.response.defer()
					self.stop()

			view = ActionView(players_ids=list(state["players"].keys()))
			view.msg = game_msg

			# Embed tour
			note = f"Tour {state['turn']} — Au tour de {cur_user.display_name}."
			await safe_edit(game_msg, embed=await make_game_embed(note), view=view)

			# Action du bot
			if cur_user.bot:
				await asyncio.sleep(1.0)
				action = "shoot" if random.random() < 0.8 else "pass"
				view.action = (action, None)
			else:
				await view.wait()

			act_name, _ = view.action or ("pass", None)

			# Actions
			if act_name == "shoot":
				chamber = barillet.pop(0)
				if chamber:
					dmg = 1
					if state["scie_flags"].get(cur_id):
						dmg += 1
						state["scie_flags"][cur_id] = False
					state["players"][cur_id]["hp"] -= dmg
					await safe_send(channel, f"💥 BANG! {cur_user.display_name} s'est tiré dessus et perd {dmg} ❤️.")
					if state["players"][cur_id]["hp"] <= 0:
						state["players"][cur_id]["alive"] = False
						state["winner"] = opp_id
						finished = True
						await safe_send(channel, f"💀 {cur_user.display_name} est éliminé! {state['players'][opp_id]['user'].display_name} gagne.")
						break
				else:
					await safe_send(channel, f"🔫 *Click* — {cur_user.display_name} est sauf.")
			else:
				await safe_send(channel, f"⏭️ {cur_user.display_name} passe.")

			# Swap joueur
			state["current_player"] = opp_id
			await asyncio.sleep(1.0)

		# Fin de partie
		summary = "\n".join([f"**{p['user'].display_name}** — ❤️ {p['hp']} — {'Vivant' if p['alive'] else 'Éliminé'}" for p in state["players"].values()])
		final_embed = discord.Embed(title="🏁 Fin de la partie — Buckshot Roulette", description=summary, color=discord.Color.gold())
		await safe_edit(game_msg, embed=final_embed, view=None)

		# Nettoyer session
		if guild_id:
			self.active_sessions.discard(guild_id)


    # ────────────────────────────────────────────────────────────────────────────
    # ▶️ Core du jeu (tour par tour, objets, barillet)
    # ────────────────────────────────────────────────────────────────────────────
    async def _start_game(self, channel, players: List[discord.abc.User], invite_msg, guild_id: Optional[int]):
        """
        Lance la partie. players = [joueur1, joueur2] (joueur2 peut être le bot).
        Utilise Supabase pour enregistrer la session si nécessaire.
        """
        # TODO: Implémentation complète des tours, actions, barillet et objets
        # On peut reprendre la logique détaillée de ton précédent code, avec:
        # - make_barillet() pour le barillet
        # - apply_item() pour objets
        # - tour par tour avec buttons et embed
        # - gestion solo vs bot
        # - mise à jour Supabase session/players si voulu
        await safe_send(channel, "🎲 Partie Buckshot Roulette lancée ! (fonctionnalité tour par tour à compléter)")
        if guild_id:
            self.active_sessions.discard(guild_id)

    # ────────────────────────────────────────────────────────────────────────────
    # Helper pour répondre selon type ctx_or_interaction
    # ────────────────────────────────────────────────────────────────────────────
    async def _respond(self, ctx_or_interaction, content: str, ephemeral: bool = False):
        if isinstance(ctx_or_interaction, commands.Context):
            return await safe_send(ctx_or_interaction.channel, content)
        else:
            return await safe_followup(ctx_or_interaction, content=content)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Buckshot(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
