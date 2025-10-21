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
from typing import Optional, List, Dict, Any
import asyncio
import random
import json
import os
from utils.discord_utils import safe_send, safe_edit, safe_followup
from supabase import create_client, Client


DEFAULT_HP = 3
CHAMBRE_COUNT = 6
MIN_BULLETS = 1
MAX_BULLETS = 5

# Load items (fallback built-in if file missing)
try:
    with open("data/buckshot_items.json", "r", encoding="utf-8") as f:
        ITEMS = json.load(f)
except Exception:
    ITEMS = {
        "cigarette": {"name": "Cigarette", "desc": "+1 HP", "emoji": "🚬"},
        "biere": {"name": "Bière", "desc": "Retire une balle du barillet", "emoji": "🍺"},
        "loupe": {"name": "Loupe", "desc": "Regarde la prochaine chambre", "emoji": "🔍"},
        "menottes": {"name": "Menottes", "desc": "Adversaire perd son prochain tour", "emoji": "⛓️"},
        "scie": {"name": "Scie", "desc": "+1 dégât au prochain tir", "emoji": "🪚"},
        "adrenaline": {"name": "Adrénaline", "desc": "Joue deux actions ce tour", "emoji": "⚡"}
    }

# Small helpers
def make_barillet(min_bullets=MIN_BULLETS, max_bullets=MAX_BULLETS, chamber_count=CHAMBRE_COUNT):
    bullets = random.randint(min_bullets, max_bullets)
    arr = [True] * bullets + [False] * (chamber_count - bullets)
    random.shuffle(arr)
    return arr

def hp_bar(hp: int, max_hp: int = 5) -> str:
    hp = max(0, min(hp, max_hp))
    full = "❤️"
    empty = "🤍"
    return full * hp + empty * (max_hp - hp)

def barillet_display(barillet: List[bool]) -> str:
    # show first 6 chambers (or pad)
    symbols = []
    for b in barillet[:CHAMBRE_COUNT]:
        symbols.append("💥" if b else "❌")
    # if shorter, pad
    if len(symbols) < CHAMBRE_COUNT:
        symbols += ["❌"] * (CHAMBRE_COUNT - len(symbols))
    return " ".join(f"[{s}]" for s in symbols)

# Supabase helpers
class SupabaseClient:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            self.client = None
        else:
            self.client: Client = create_client(url, key)

    def upsert_player(self, user_id: int) -> None:
        if not getattr(self, "client", None):
            return
        table = self.client.table("buckshot_players")
        # create default record if missing
        data = {
            "user_id": user_id,
            "hp": DEFAULT_HP,
            "money": 0,
            "items": [],
            "wins": 0,
            "losses": 0
        }
        try:
            table.upsert(data).execute()
        except Exception:
            pass

    def create_session(self, guild_id: Optional[int], channel_id: int, player1_id: int, player2_id: int) -> Optional[Dict[str, Any]]:
        if not getattr(self, "client", None):
            return None
        try:
            row = {
                "guild_id": guild_id,
                "channel_id": channel_id,
                "player1_id": player1_id,
                "player2_id": player2_id,
                "current_player": player1_id,
                "turn": 0,
                "state": {},
                "started_at": None
            }
            res = self.client.table("buckshot_sessions").insert(row).execute()
            return res.data[0] if res.data else None
        except Exception:
            return None

    def update_session_state(self, session_id: int, state: dict, turn: int, current_player: int) -> None:
        if not getattr(self, "client", None):
            return
        try:
            self.client.table("buckshot_sessions").update({"state": state, "turn": turn, "current_player": current_player}).eq("id", session_id).execute()
        except Exception:
            pass

    def end_session(self, session_id: int) -> None:
        if not getattr(self, "client", None):
            return
        try:
            self.client.table("buckshot_sessions").delete().eq("id", session_id).execute()
        except Exception:
            pass

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class Buckshot(commands.Cog):
    """Buckshot Roulette — Cog refactorisé"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions: Dict[int, Dict[str, Any]] = {}  # guild_id -> session metadata
        self.sup = SupabaseClient()
        self.max_hp = 5

    # -------------------- Commands --------------------
    @commands.command(name="buckshot")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_buckshot(self, ctx: commands.Context, target: Optional[discord.Member] = None):
        await self._start_request(ctx, target)

    @app_commands.command(name="buckshot", description="Joue au Buckshot Roulette (solo ou défie quelqu'un)")
    @app_commands.describe(target="Mentionnez un joueur pour le défier (optionnel)")
    async def slash_buckshot(self, interaction: discord.Interaction, target: Optional[discord.Member] = None):
        await interaction.response.defer()
        await self._start_request(interaction, target)

    # -------------------- Start / Invitation --------------------
    async def _start_request(self, ctx_or_interaction, target: Optional[discord.Member]):
        guild = getattr(ctx_or_interaction, "guild", None)
        guild_id = guild.id if guild else None
        channel = getattr(ctx_or_interaction, "channel", None)

        author = ctx_or_interaction.author if isinstance(ctx_or_interaction, commands.Context) else ctx_or_interaction.user

        if guild_id and guild_id in self.sessions:
            return await self._respond(ctx_or_interaction, "⚠️ Une partie est déjà en cours sur ce serveur.", ephemeral=True)

        if target and target.bot and target != self.bot.user:
            return await self._respond(ctx_or_interaction, "🔒 Tu ne peux pas défier un bot tiers.", ephemeral=True)

        # prepare invite embed
        title = "🎯 Buckshot Roulette — Défi" if target else "🎯 Buckshot Roulette — Solo"
        desc = f"{author.mention} propose une partie."
        if target:
            desc += f" {target.mention}, accepte-tu ?"
        else:
            desc += " Clique sur Jouer pour commencer contre le bot."

        embed = discord.Embed(title=title, description=desc, color=discord.Color.blurple())

        class InviteView(discord.ui.View):
            def __init__(self, timeout=30):
                super().__init__(timeout=timeout)
                self.result = None

            @discord.ui.button(label="✅ Accepter", style=discord.ButtonStyle.success)
            async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not target:
                    return await interaction.response.send_message("Ce bouton n'est pas applicable.", ephemeral=True)
                if interaction.user.id != target.id:
                    return await interaction.response.send_message("🔒 Seul le défié peut accepter.", ephemeral=True)
                self.result = "accept"
                await interaction.response.edit_message(view=self)
                self.stop()

            @discord.ui.button(label="🟢 Jouer (solo)", style=discord.ButtonStyle.primary)
            async def solo(self, interaction: discord.Interaction, button: discord.ui.Button):
                if target:
                    return await interaction.response.send_message("Ce bouton est pour le solo uniquement.", ephemeral=True)
                if interaction.user.id != author.id:
                    return await interaction.response.send_message("🔒 Seul l'initiateur peut démarrer.", ephemeral=True)
                self.result = "solo"
                await interaction.response.edit_message(view=self)
                self.stop()

            @discord.ui.button(label="❌ Refuser", style=discord.ButtonStyle.danger)
            async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not target:
                    return await interaction.response.send_message("Ce bouton n'est pas applicable.", ephemeral=True)
                if interaction.user.id != target.id:
                    return await interaction.response.send_message("🔒 Seul le défié peut refuser.", ephemeral=True)
                self.result = "refuse"
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

        view = InviteView(timeout=30)
        if isinstance(ctx_or_interaction, commands.Context):
            msg = await safe_send(channel, embed=embed, view=view)
        else:
            msg = await safe_followup(ctx_or_interaction, embed=embed, view=view)

        await view.wait()
        res = view.result

        if res == "accept":
            players = [author, target]
            await safe_edit(msg, embed=discord.Embed(title="⚔️ Début du duel", description=f"{author.mention} vs {target.mention}", color=discord.Color.dark_teal()), view=None)
            if guild_id:
                self.sessions[guild_id] = {"channel": channel}
            await asyncio.sleep(0.8)
            await self._start_game(channel, players, msg, guild_id)
        elif res == "solo":
            players = [author, self.bot.user]
            await safe_edit(msg, embed=discord.Embed(title="🤖 Solo contre le bot", description=f"{author.mention} vs {self.bot.user.mention}", color=discord.Color.dark_teal()), view=None)
            if guild_id:
                self.sessions[guild_id] = {"channel": channel}
            await asyncio.sleep(0.8)
            await self._start_game(channel, players, msg, guild_id)
        else:
            content = "❌ Défi refusé." if res == "refuse" else "✖️ Défi annulé." if res == "cancel" else "⏰ Temps écoulé."
            await safe_edit(msg, embed=discord.Embed(title="Fin de la demande", description=content, color=discord.Color.red()), view=None)

    # -------------------- Core game --------------------
    async def _start_game(self, channel: discord.abc.Messageable, players: List[discord.User], invite_msg: discord.Message, guild_id: Optional[int]):
        # Persist players in Supabase
        for p in players:
            if isinstance(p, discord.User):
                self.sup.upsert_player(p.id)

        # Build in-memory state
        p1, p2 = players
        state = {
            "turn": 0,
            "barillet": make_barillet(),
            "current": p1.id,
            "players": {
                p1.id: {"user": p1, "hp": DEFAULT_HP, "items": [], "alive": True},
                p2.id: {"user": p2, "hp": DEFAULT_HP, "items": [], "alive": True},
            },
            "logs": [],
            "session_id": None
        }

        # store session to supabase (best-effort)
        sess = self.sup.create_session(guild_id, getattr(channel, "id", None) or 0, p1.id, p2.id)
        if sess and "id" in sess:
            state["session_id"] = sess["id"]

        # distribute items randomly
        item_keys = list(ITEMS.keys())
        for pid in state["players"]:
            n = random.choice([1, 1, 2])
            state["players"][pid]["items"] = random.sample(item_keys, k=n)

        # Build initial embed
        async def build_embed(note: str = "") -> discord.Embed:
            turn = state["turn"]
            title = f"🎲 Buckshot Roulette — Tour {turn}" if turn else "🎲 Buckshot Roulette — Début"
            desc = note or "Fais ton choix : Tirer / Passer / Utiliser un objet"
            embed = discord.Embed(title=title, description=desc, color=discord.Color.dark_gold())

            # Player fields
            for pid, pdata in state["players"].items():
                u = pdata["user"]
                hp = pdata["hp"]
                items = pdata.get("items", [])
                item_display = " ".join(ITEMS[k].get("emoji", "") + " " + ITEMS[k].get("name", k) for k in items) if items else "—"
                embed.add_field(name=f"{u.display_name}", value=f"{hp_bar(hp, self.max_hp)}\nItems: {item_display}", inline=False)

            # barillet
            embed.add_field(name="🔫 Barillet", value=barillet_display(state["barillet"]), inline=False)

            embed.set_footer(text=f"Au tour de : {state['players'][state['current']]['user'].display_name} | Tour {state['turn']}")
            return embed

        # Send initial message
        state["turn"] = 0
        last_embed = await build_embed("Début de la partie — bonne chance !")
        game_msg = await safe_send(channel, embed=last_embed)

        finished = False

        # Action view (shoot / pass / use item)
        class ActionView(discord.ui.View):
            def __init__(self, allowed_user_id: int, timeout: int = 40):
                super().__init__(timeout=timeout)
                self.allowed = allowed_user_id
                self.choice = None
                self.payload = None

            def _check(self, interaction: discord.Interaction):
                return interaction.user.id == self.allowed

            @discord.ui.button(label="🔫 Tirer", style=discord.ButtonStyle.danger)
            async def shoot(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not self._check(interaction):
                    return await interaction.response.send_message("🔒 Ce n'est pas ton tour.", ephemeral=True)
                self.choice = "shoot"
                await interaction.response.defer()
                self.stop()

            @discord.ui.button(label="⏭️ Passer", style=discord.ButtonStyle.secondary)
            async def passe(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not self._check(interaction):
                    return await interaction.response.send_message("🔒 Ce n'est pas ton tour.", ephemeral=True)
                self.choice = "pass"
                await interaction.response.defer()
                self.stop()

            @discord.ui.button(label="🧰 Utiliser un objet", style=discord.ButtonStyle.primary)
            async def use_item(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not self._check(interaction):
                    return await interaction.response.send_message("🔒 Ce n'est pas ton tour.", ephemeral=True)
                # open a simple modal-ish flow via ephemeral messages to choose item
                player_items = state[interaction.user.id]["items"]
                if not player_items:
                    await interaction.response.send_message("Tu n'as pas d'objets.", ephemeral=True)
                    return
                opts = "\n".join(f"{i+1}. {ITEMS[it]['emoji']} {ITEMS[it]['name']} — {ITEMS[it]['desc']}" for i, it in enumerate(player_items))
                await interaction.response.send_message(f"Choisis l'objet à utiliser (répond par le numéro dans le chat privé) :\n{opts}", ephemeral=True)
                try:
                    def check(m: discord.Message):
                        return m.author.id == interaction.user.id and isinstance(m.channel, discord.DMChannel)
                    dm = await interaction.user.create_dm()
                    reply = await self.bot.wait_for('message', check=check, timeout=25)
                    idx = int(reply.content.strip()) - 1
                    if idx < 0 or idx >= len(player_items):
                        await dm.send("Numéro invalide — action annulée.")
                        return
                    chosen = player_items[idx]
                    self.choice = "use"
                    self.payload = chosen
                    await dm.send(f"✅ Tu as utilisé : {ITEMS[chosen]['emoji']} {ITEMS[chosen]['name']}")
                    self.stop()
                except Exception:
                    # timeout or parsing
                    try:
                        await interaction.user.send("Temps écoulé ou entrée invalide — annulation.")
                    except Exception:
                        pass

        # Game loop
        while not finished:
            state["turn"] += 1
            cur_id = state["current"]
            cur = state["players"][cur_id]
            opp_id = [x for x in state["players"].keys() if x != cur_id][0]
            opp = state["players"][opp_id]

            # menottes check (simple flag stored in state)
            if state.get("menotte_until") == cur_id:
                note = f"🔒 {cur['user'].display_name} est menotté et perd ce tour."
                state["menotte_until"] = None
                state["current"] = opp_id
                await safe_edit(game_msg, embed=await build_embed(note), view=None)
                await asyncio.sleep(1.0)
                continue

            # prepare view for current player
            view = ActionView(allowed_user_id=cur_id)
            await safe_edit(game_msg, embed=await build_embed(f"Tour {state['turn']} — Au tour de {cur['user'].display_name}"), view=view)

            # If bot, choose automatically
            if cur['user'].bot:
                await asyncio.sleep(1.0)
                choice = "shoot" if random.random() < 0.8 else "pass"
                payload = None
            else:
                await view.wait()
                choice = view.choice or "pass"
                payload = view.payload

            # Execute action
            note = ""
            if choice == "shoot":
                # pop first chamber or regenerate if empty
                if not state["barillet"]:
                    state["barillet"] = make_barillet()
                chamber = state["barillet"].pop(0)
                if chamber:
                    dmg = 1
                    if state.get("scie_flags", {}).get(cur_id):
                        dmg += 1
                        state["scie_flags"][cur_id] = False
                    cur["hp"] -= dmg
                    note = f"💥 BANG! {cur['user'].display_name} s'est tiré dessus et perd {dmg} ❤️."
                    if cur["hp"] <= 0:
                        cur["alive"] = False
                        finished = True
                        state["winner"] = opp_id
                else:
                    note = f"🔫 *Click* — {cur['user'].display_name} est sauf."

            elif choice == "pass":
                note = f"⏭️ {cur['user'].display_name} passe son tour."

            elif choice == "use":
                item_key = payload
                # remove item from inventory (first occurrence)
                try:
                    cur_items = cur.get("items", [])
                    cur_items.remove(item_key)
                except Exception:
                    pass
                # apply effect
                if item_key == "cigarette":
                    cur["hp"] = min(self.max_hp, cur["hp"] + 1)
                    note = f"{cur['user'].display_name} fume une cigarette et récupère ❤️1."
                elif item_key == "biere":
                    if True in state["barillet"]:
                        idx = state["barillet"].index(True)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = Buckshot(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)

