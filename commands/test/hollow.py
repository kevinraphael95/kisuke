# ────────────────────────────────────────────────────────────────────────────────
# 📌 hollow.py — Commande interactive !hollow
# Objectif : Faire apparaître un Hollow, le joueur peut l’attaquer en dépensant 50 reiatsu
#           et doit accomplir 3 tâches intégrées pour le vaincre.
# Catégorie : Hollow
# Accès : Public
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
from discord.ui import View, Button
from discord import Embed
import os
import random
import traceback
from utils.discord_utils import safe_send
from supabase_client import supabase
import asyncio
import json

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Chargement des personnages (pour bmoji)
# ────────────────────────────────────────────────────────────────────────────────
DATA_JSON_PATH = os.path.join("data", "bleach_emojis.json")
def load_characters():
    with open(DATA_JSON_PATH, encoding="utf-8") as f:
        return json.load(f)

# ────────────────────────────────────────────────────────────────────────────────
# 📂 Constantes
# ────────────────────────────────────────────────────────────────────────────────
HOLLOW_IMAGE_PATH = os.path.join("data", "hollows", "hollow0.jpg")
REIATSU_COST = 1

# ────────────────────────────────────────────────────────────────────────────────
# 🔹 Fonctions des mini‑jeux (tâches)
# ────────────────────────────────────────────────────────────────────────────────

async def lancer_emoji(interaction: discord.Interaction) -> bool:
    pool = ["💀", "🌀", "🔥", "🌪️", "🌟", "🍥", "🍡", "🧊", "❄️", "💨"]
    sequence = random.sample(pool, 3)
    autres = [e for e in pool if e not in sequence]
    mix = sequence + random.sample(autres, 2)
    random.shuffle(mix)

    msg = await interaction.followup.send(
        f"🔁 Reproduis cette séquence : {' → '.join(sequence)}\nTu as 2 minutes !"
    )
    for e in mix:
        try: await msg.add_reaction(e)
        except: pass

    reponses = {}
    def check(r, u):
        if u.bot or r.message.id != msg.id:
            return False
        if u.id not in reponses:
            reponses[u.id] = []
        idx = len(reponses[u.id])
        if str(r.emoji) == sequence[idx]:
            reponses[u.id].append(str(r.emoji))
        return reponses[u.id] == sequence

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=120)
        await interaction.followup.send(f"✅ Séquence correcte {user.mention} !", ephemeral=True)
        return True
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Personne n'a réussi.", ephemeral=True)
        return False

async def lancer_reflexe(interaction: discord.Interaction) -> bool:
    compte = ["5️⃣", "4️⃣", "3️⃣", "2️⃣", "1️⃣"]
    msg = await interaction.followup.send("🕒 Clique dans l’ordre `5️⃣ 4️⃣ 3️⃣ 2️⃣ 1️⃣` !")
    for e in compte:
        await msg.add_reaction(e)

    reponses = {}
    def check(r, u):
        if u.bot or r.message.id != msg.id:
            return False
        if u.id not in reponses:
            reponses[u.id] = []
        idx = len(reponses[u.id])
        if str(r.emoji) == compte[idx]:
            reponses[u.id].append(str(r.emoji))
        return reponses[u.id] == compte

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=20)
        await interaction.followup.send(f"⚡ Réflexe parfait {user.mention} !", ephemeral=True)
        return True
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Aucun réflexe parfait.", ephemeral=True)
        return False

async def lancer_fleche(interaction: discord.Interaction) -> bool:
    fleches = ["⬅️", "⬆️", "⬇️", "➡️"]
    sequence = [random.choice(fleches) for _ in range(5)]
    tmp = await interaction.followup.send(f"🧭 Mémorise : `{' '.join(sequence)}` (5 s)")
    await asyncio.sleep(5)
    await tmp.delete()
    msg = await interaction.followup.send("🔁 Reproduis la séquence en cliquant :")

    for e in fleches:
        await msg.add_reaction(e)

    reponses = {}
    def check(r, u):
        if u.bot or r.message.id != msg.id:
            return False
        if u.id not in reponses:
            reponses[u.id] = []
        pos = len(reponses[u.id])
        if pos >= len(sequence): return False
        attendu = sequence[pos]
        if str(r.emoji) == attendu:
            reponses[u.id].append(str(r.emoji))
            asyncio.create_task(msg.remove_reaction(r.emoji, u))
            return len(reponses[u.id]) == len(sequence)
        else:
            reponses[u.id] = []
            return False

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=30)
        await interaction.followup.send(f"✅ Bien joué {user.mention} !", ephemeral=True)
        return True
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Personne n'a réussi.", ephemeral=True)
        return False

async def lancer_infusion(interaction: discord.Interaction) -> bool:
    await interaction.followup.send("🔵 Prépare-toi à synchroniser ton Reiatsu...")
    await asyncio.sleep(2)
    msg = await interaction.followup.send("🔵")
    for _ in range(3):
        await asyncio.sleep(0.6); await msg.edit(content="🔵🔵")
        await asyncio.sleep(0.6); await msg.edit(content="🔵🔵🔵")
    await asyncio.sleep(0.5); await msg.edit(content="🔴")
    await msg.add_reaction("⚡")
    start = discord.utils.utcnow()

    def check(r, u):
        if u.bot or r.message.id != msg.id or str(r.emoji) != "⚡":
            return False
        delta = (discord.utils.utcnow() - start).total_seconds()
        return 0.8 <= delta <= 1.2

    try:
        reaction, user = await interaction.client.wait_for("reaction_add", check=check, timeout=2)
        await interaction.followup.send(f"✅ Synchronisation parfaite, {user.mention} !", ephemeral=True)
        return True
    except asyncio.TimeoutError:
        await interaction.followup.send("❌ Échec, Reiatsu instable.", ephemeral=True)
        return False

class EmojiBoutons(discord.ui.View):
    def __init__(self, vrai: bool):
        super().__init__(timeout=15)
        self.vrai = vrai
        self.repondu = False

    @discord.ui.button(label="✅ Oui", style=discord.ButtonStyle.success)
    async def oui(self, inter, btn):
        if self.repondu: return
        self.repondu = True
        await self.verifie(inter, True)

    @discord.ui.button(label="❌ Non", style=discord.ButtonStyle.danger)
    async def non(self, inter, btn):
        if self.repondu: return
        self.repondu = True
        await self.verifie(inter, False)

    async def verifie(self, inter, rep):
        if rep == self.vrai:
            await inter.response.send_message("✅ Bonne réponse !", ephemeral=True)
        else:
            await inter.response.send_message("❌ Mauvaise réponse.", ephemeral=True)
        self.stop()

async def lancer_emoji9(interaction: discord.Interaction) -> bool:
    groupes = [["🍎","🍅"],["☁️","🌥️"],["☘️","🍀"],["🌺","🌸"],
               ["👜","💼"],["🌹","🌷"],["🤞","✌️"],["✊","👊"],
               ["😕","😐"],["🌟","⭐"],["🦝","🐨"],["🔒","🔓"],
               ["🏅","🥇"],["🌧️","🌨️"],["🐆","🐅"],["🙈","🙊"],
               ["🐋","🐳"],["🐢","🐊"]]
    base, intrus = random.choice(groupes)
    has_intrus = random.choice([True, False])
    emojis = [base]*9
    if has_intrus:
        emojis[random.randint(0,8)] = intrus
    random.shuffle(emojis)
    ligne = "".join(emojis)

    embed = Embed(title="🔎 Tous identiques ?", description=f"{ligne}\n✅ si oui, ❌ si non", color=discord.Color.orange())
    view = EmojiBoutons(vrai=(not has_intrus))
    await interaction.followup.send(embed=embed, view=view)
    try:
        await inter.client.wait_for("interaction", timeout=15)
        return True
    except asyncio.TimeoutError:
        return False

async def lancer_bmoji(interaction: discord.Interaction) -> bool:
    characters = load_characters()
    pers = random.choice(characters)
    nom = pers["nom"]
    emojis = random.sample(pers["emojis"], k=min(3, len(pers["emojis"])))
    autres = [c["nom"] for c in characters if c["nom"] != nom]
    distracteurs = random.sample(autres, 3)
    options = distracteurs + [nom]
    random.shuffle(options)
    lettres = ["🇦","🇧","🇨","🇩"]
    bonne = lettres[options.index(nom)]

    embed = Embed(title="🔍 Devine le perso", description="Emoji➤Perso", color=0x1abc9c)
    embed.add_field(name="Emojis", value=" ".join(emojis), inline=False)
    embed.add_field(name="Choix", value="\n".join(f"{lettres[i]}: {options[i]}" for i in range(4)), inline=False)
    embed.set_footer(text="Réagis 🇦 🇧 🇨 ou 🇩")
    message = await interaction.followup.send(embed=embed)
    for e in lettres:
        await message.add_reaction(e)

    def check(r, u):
        return u == interaction.user and r.message.id == message.id and str(r.emoji) in lettres

    try:
        r, u = await interaction.client.wait_for("reaction_add", check=check, timeout=30)
        if str(r.emoji) == bonne:
            await interaction.followup.send(f"✅ Bravo {u.mention} !", ephemeral=True)
            return True
        else:
            await interaction.followup.send(f"❌ Mauvaise réponse.", ephemeral=True)
            return False
    except asyncio.TimeoutError:
        await interaction.followup.send("⌛ Temps écoulé.", ephemeral=True)
        return False

# ────────────────────────────────────────────────────────────────────────────────
# 🔁 Fonction pour lancer 3 tâches aléatoires
# ────────────────────────────────────────────────────────────────────────────────

TACHES_DISPONIBLES = [
    lancer_emoji,
    lancer_reflexe,
    lancer_fleche,
    lancer_infusion,
    lancer_emoji9,
    lancer_bmoji,
]

async def lancer_3_taches_aleatoires(interaction: discord.Interaction, message: discord.Message, embed: discord.Embed) -> bool:
    taches = random.sample(TACHES_DISPONIBLES, 3)
    for idx, tache in enumerate(taches, 1):
        embed.description = f"⚔️ Combat contre le Hollow...\n🧪 Épreuve {idx}/3 en cours..."
        embed.set_footer(text=f"Épreuve {idx}/3")
        await message.edit(embeds=[embed])

        success = await tache(interaction)
        if not success:
            embed.description = f"💀 Tu as échoué à l’épreuve {idx}/3."
            embed.set_footer(text="Défaite…")
            await message.edit(embeds=[embed])
            return False

        embed.description = f"✅ Épreuve {idx}/3 réussie !"
        await message.edit(embeds=[embed])
        await asyncio.sleep(1.2)

    embed.description = f"🎉 Toutes les épreuves ont été réussies !"
    embed.set_footer(text="Victoire !")
    await message.edit(embeds=[embed])
    return True


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Vue avec bouton d’attaque
# ────────────────────────────────────────────────────────────────────────────────

class HollowView(View):
    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.attacked = False
        self.message = None

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass

    @discord.ui.button(label=f"Attaquer ({REIATSU_COST} reiatsu)", style=discord.ButtonStyle.red)
    async def attack(self, inter: discord.Interaction, btn):
        if inter.user.id != self.author_id:
            await inter.response.send_message("❌ Ce bouton n’est pas pour toi.", ephemeral=True); return
        if self.attacked:
            await inter.response.send_message("⚠️ Tu as déjà attaqué.", ephemeral=True); return

        await inter.response.defer(thinking=True)
        uid = str(inter.user.id)

        try:
            resp = supabase.table("reiatsu").select("points").eq("user_id", uid).execute()
            if not resp.data or resp.data[0].get("points", 0) < REIATSU_COST:
                await inter.followup.send(f"❌ Il faut {REIATSU_COST} points de reiatsu.", ephemeral=True); return

            new = resp.data[0]["points"] - REIATSU_COST
            upd = supabase.table("reiatsu").update({"points": new}).eq("user_id", uid).execute()
            if not upd.data:
                await inter.followup.send("⚠️ Erreur mise à jour reiatsu.", ephemeral=True); return

            self.attacked = True

            embed = self.message.embeds[0]
            embed.description = f"⚔️ {inter.user.display_name} attaque le Hollow...\nPrépare-toi aux épreuves !"
            embed.set_footer(text="Combat en cours")
            await self.message.edit(embeds=[embed], view=self)

            success = await lancer_3_taches_aleatoires(inter, self.message, embed)

            result_embed = discord.Embed(
                title="🎯 Résultat du combat",
                description="🎉 Tu as vaincu le Hollow !" if success else "💀 Tu as échoué à vaincre le Hollow.",
                color=discord.Color.green() if success else discord.Color.red()
            )
            result_embed.set_footer(text=f"Combat de {inter.user.display_name}")

            await self.message.edit(embeds=[embed, result_embed], view=self)

        except Exception:
            traceback.print_exc()
            await inter.followup.send("⚠️ Échec inattendu.", ephemeral=True)


# ────────────────────────────────────────────────────────────────────────────────
# 🧠 Cog principal — HollowCommand
# ────────────────────────────────────────────────────────────────────────────────

class HollowCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="hollow", help="Fais apparaître un Hollow à attaquer")
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.user)
    async def hollow(self, ctx: commands.Context):
        if not os.path.isfile(HOLLOW_IMAGE_PATH):
            await safe_send(ctx, "❌ Image du Hollow introuvable.")
            return

        file = discord.File(HOLLOW_IMAGE_PATH, filename="hollow.jpg")
        embed = Embed(title="👹 Un Hollow est apparu !",
                      description=f"Attaque-le pour {REIATSU_COST} reiatsu et réussis 3 tâches.",
                      color=discord.Color.dark_red())
        embed.set_image(url="attachment://hollow.jpg")
        embed.set_footer(text="Tu as 60 secondes pour cliquer sur Attaquer.")
        view = HollowView(author_id=ctx.author.id)
        msg = await ctx.send(embed=embed, file=file, view=view)
        view.message = msg




# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = HollowCommand(bot)
    for command in cog.get_commands():
        command.category = "Hollow"
    await bot.add_cog(cog)
