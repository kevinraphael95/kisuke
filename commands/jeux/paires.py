# ────────────────────────────────────────────────────────────────────────────────
# 📌 memory_game.py — Jeu de paires (Memory) avec Discord
# Objectif : Jeu de memory temps réel avec emojis et thèmes
# Catégorie : Jeu
# Accès : Tous
# Cooldown : 1 utilisation / 10 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

# ────────────────────────────────────────────────────────────────────────────────
# 📦 Imports nécessaires
# ────────────────────────────────────────────────────────────────────────────────
import discord
from discord.ext import commands
from discord.ui import View, Button
import random
import asyncio
from utils.discord_utils import safe_send, safe_edit

# ────────────────────────────────────────────────────────────────────────────────
# 🎨 Thèmes possibles
# ────────────────────────────────────────────────────────────────────────────────
THEMES = {
    "fruits": ["🍎","🍌","🍇","🍓","🍍","🥭","🍉","🍑"],
    "animaux": ["🐶","🐱","🐭","🐰","🦊","🐼","🦁","🐸"],
    "couleurs": ["🔴","🟢","🔵","🟡","🟣","🟠","⚫","⚪"]
}

# ────────────────────────────────────────────────────────────────────────────────
# 🧩 Memory Game View
# ────────────────────────────────────────────────────────────────────────────────
class MemoryGameView(View):
    def __init__(self, ctx_or_interaction, theme="fruits", size=4, mode="solo"):
        super().__init__(timeout=180)
        self.ctx_or_interaction = ctx_or_interaction
        self.mode = mode.lower()
        self.theme = theme if theme in THEMES else "fruits"
        self.size = size
        self.cards = THEMES[self.theme][: (size*size)//2] * 2
        random.shuffle(self.cards)
        self.board = [self.cards[i*self.size:(i+1)*self.size] for i in range(self.size)]
        self.buttons = {}
        self.flipped = []       # [(r,c,emoji)]
        self.found = set()      # positions déjà trouvées
        self.errors = {}        # erreurs par joueur
        self.scores = {}        # paires trouvées par joueur (multi)
        self.create_buttons()

    # ────────────────────────────────────────────────────────────────────────────
    # 🧱 Création des boutons
    # ────────────────────────────────────────────────────────────────────────────
    def create_buttons(self):
        for r in range(self.size):
            for c in range(self.size):
                btn = Button(label="❓", style=discord.ButtonStyle.secondary, row=r)
                btn.callback = self.make_callback(r, c)
                self.add_item(btn)
                self.buttons[(r, c)] = btn

    # ────────────────────────────────────────────────────────────────────────────
    # 🧠 Gestion du clic sur une carte
    # ────────────────────────────────────────────────────────────────────────────
    def make_callback(self, r, c):
        async def callback(interaction: discord.Interaction):
            # Mode solo : seul le joueur qui a lancé la partie peut jouer
            if self.mode == "solo":
                player_id = getattr(self.ctx_or_interaction.user, "id", getattr(self.ctx_or_interaction.author, "id", None))
                if interaction.user.id != player_id:
                    return await interaction.response.send_message("❌ Ce jeu est en mode **solo**, seul le joueur peut cliquer.", ephemeral=True)

            pos = (r, c)
            if pos in self.found or any(pos == f[:2] for f in self.flipped):
                return  # déjà révélée ou cliquée
            if len(self.flipped) >= 2:
                return await interaction.response.defer()

            emoji = self.board[r][c]
            btn = self.buttons[pos]
            btn.label = emoji
            btn.style = discord.ButtonStyle.primary
            self.flipped.append((r, c, emoji))
            await safe_edit(interaction.message, view=self)

            # Si deux cartes sont retournées
            if len(self.flipped) == 2:
                await asyncio.sleep(1.2)
                (r1, c1, e1), (r2, c2, e2) = self.flipped
                if e1 == e2:
                    # ✅ Paire trouvée
                    for rr, cc in [(r1, c1), (r2, c2)]:
                        self.buttons[(rr, cc)].style = discord.ButtonStyle.success
                        self.buttons[(rr, cc)].disabled = True
                    self.found.update({(r1, c1), (r2, c2)})

                    user_id = interaction.user.id
                    if self.mode == "multi":
                        self.scores[user_id] = self.scores.get(user_id, 0) + 1
                else:
                    # ❌ Erreur (solo : compteur de fautes)
                    user_id = interaction.user.id
                    self.errors[user_id] = self.errors.get(user_id, 0) + 1
                    for rr, cc in [(r1, c1), (r2, c2)]:
                        self.buttons[(rr, cc)].label = "❓"
                        self.buttons[(rr, cc)].style = discord.ButtonStyle.secondary

                self.flipped.clear()
                await safe_edit(interaction.message, view=self)

                # 🎯 Vérification fin de partie
                if len(self.found) == self.size * self.size:
                    if self.mode == "solo":
                        user_id = list(self.errors.keys())[0] if self.errors else None
                        msg = f"🎉 **Partie terminée !** Toutes les paires ont été trouvées !"
                        if user_id:
                            msg += f"\n💡 Tu as fait **{self.errors[user_id]} erreurs**."
                        else:
                            msg += "\nParfait ! Aucune erreur 👏"
                    else:
                        if self.scores:
                            classement = sorted(self.scores.items(), key=lambda x: -x[1])
                            msg = "🎉 **Partie terminée !** Voici le classement :\n\n"
                            for i, (uid, score) in enumerate(classement):
                                msg += f"**{i+1}.** <@{uid}> — {score} paire(s)\n"
                            msg += "\n🏆 Bravo à tous les participants !"
                        else:
                            msg = "🎉 Partie terminée ! Aucune paire trouvée... 😅"

                    await safe_edit(interaction.message, content=msg, view=None)

        return callback

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal
# ────────────────────────────────────────────────────────────────────────────────
class MemoryGame(commands.Cog):
    """Jeu de paires Memory — Mode solo (moins d’erreurs) ou multi (plus de paires)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @discord.app_commands.command(
        name="paires",
        description="Jouer au Memory Game (solo ou multi)"
    )
    async def slash_memory(self, interaction: discord.Interaction, mode: str = "solo", theme: str = "fruits"):
        mode = "multi" if mode.lower() in ["multi", "m"] else "solo"
        await interaction.response.defer()
        view = MemoryGameView(interaction, theme=theme, size=4, mode=mode)
        titre = "👤 Mode Solo" if mode == "solo" else "👥 Mode Multi"
        msg = f"🧩 **Memory Game — {titre}**\nThème : **{theme}**\n"
        msg += "🎯 Objectif : Trouver toutes les paires avec le moins d’erreurs possibles !" if mode == "solo" else "🎯 Objectif : Faire le plus de paires possibles !"
        await safe_send(interaction.channel, msg, view=view)

    # ────────────────────────────────────────────────────────────────────────────
    # 🔹 Commande PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="paires")
    async def prefix_memory(self, ctx: commands.Context, mode: str = "solo", theme: str = "fruits"):
        mode = "multi" if mode.lower() in ["multi", "m"] else "solo"
        view = MemoryGameView(ctx, theme=theme, size=4, mode=mode)
        titre = "👤 Mode Solo" if mode == "solo" else "👥 Mode Multi"
        msg = f"🧩 **Memory Game — {titre}**\nThème : **{theme}**\n"
        msg += "🎯 Objectif : Trouver toutes les paires avec le moins d’erreurs possibles !" if mode == "solo" else "🎯 Objectif : Faire le plus de paires possibles !"
        await safe_send(ctx.channel, msg, view=view)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = MemoryGame(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
