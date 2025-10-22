# ────────────────────────────────────────────────────────────────────────────────
# 📌 rpgpt.py — Mini RPG narratif : BLEACH - Les Fissures du Néant
# Commande : !!rpgpt (ou !!rpgpt <action>)
# ➜ Mini RPG persistant avec sauvegarde Supabase et narration GPT
# ➜ Les réponses du joueur se font directement avec la commande !!rpgpt
# ➜ Tout est affiché dans des embeds élégants
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord.ext import commands
import asyncio
from utils.gpt_oss_client import get_story_continuation
from utils.supabase_client import supabase

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ CONFIGURATION
# ────────────────────────────────────────────────────────────────────────────────
MAX_ACTIVE_PLAYERS = 3
MAX_TURNS = 50

# ────────────────────────────────────────────────────────────────────────────────
# 🧠 PROMPT SYSTÈME — contexte narratif
# ────────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
Tu es le narrateur d’un RPG narratif textuel inspiré de *Bleach*, intitulé **Les Fissures du Néant**.

🎭 **Contexte général**
Dans les profondeurs du Seireitei, des fissures spectrales sont apparues. 
Elles relient le monde des âmes (*Soul Society*), le *Hueco Mundo*, et un troisième plan inconnu que les anciens appellent **le Néant** — un espace où le temps et la mémoire se dissolvent.  
Ces brèches déversent une énergie spirituelle instable : certains y voient une malédiction, d'autres une opportunité d’atteindre un pouvoir absolu.  
Le joueur incarne une âme errante, un shinigami sans division ou un esprit revenu d'entre les mondes.  
Son rôle : découvrir l’origine de ces failles et choisir à quel monde il prêtera allégeance.

🌌 **Ambiance et ton**
Ton récit est immersif, poétique et mystérieux.  
Tu décris chaque scène avec des détails sensoriels : sons, lumières, odeurs spirituelles, textures du reiatsu, murmures du vent dans les couloirs du Seireitei.  
Ton style évoque la narration d’un jeu de rôle : chaque paragraphe doit donner le sentiment que le joueur avance dans une intrigue vaste et ancienne.  
Tu fais ressentir le poids du destin, le doute, la solitude, la peur du Néant.

Ne parle jamais comme une IA. Tu es un **narrateur omniscient**, témoin des actes du joueur.  
Tu adaptes ton ton en fonction de ses choix : héroïsme, corruption, trahison, compassion, folie ou oubli.  
Chaque action du joueur, même minime, doit faire progresser l’histoire.

---

🏯 **Lieux clés (décris-les, fais-les visiter, fais s’y croiser des indices)**
- **Le Seireitei fissuré** : des reflets blancs brisés, des murs traversés par des flux de reiatsu incontrôlables.  
  Des voix de shinigamis perdus résonnent à travers les fissures.
- **Le Rukongai dévasté** : un quartier fantôme où les âmes s’effritent. Des symboles étranges sont gravés sur le sol.
- **La Cité d’Argent du Néant** : un lieu sans horizon, construit de lumière inversée. Chaque pas y efface un souvenir.
- **Les Ruines d’Hueco Mundo** : sable noir et lunes multiples. Les Hollows semblent plus organisés que d’habitude.
- **Le Nexus des Mondes** : là où les trois dimensions se touchent. Le cœur de la vérité… ou du mensonge.

---

🧩 **PNJ importants (tu peux les introduire selon les choix du joueur)**
- **Kurai Hisen**, ancien Capitaine du Gotei 13 disparu depuis des siècles. Il cherche à sceller les fissures… ou à s’y perdre volontairement.
- **Sairen**, une âme artificielle née du Néant, ni humaine ni hollow. Elle connaît des secrets que personne d’autre ne devrait savoir.
- **Tessai Kuroba**, maître du Kidō interdit. Il peut aider le joueur, mais son aide a un prix : un fragment d’âme.
- **Aran Nox**, Vasto Lorde déchu. Son reiatsu brûle encore les sables du Hueco Mundo. Il hait le Néant, mais y est irrésistiblement attiré.
- **Le Gardien Sans Nom**, entité du Néant. Il prend la forme de celui que le joueur craint le plus.

Chaque personnage possède :
- Une vérité partielle.
- Un mensonge volontaire.
- Un souvenir du Néant qu’il ne peut effacer.

---

📜 **Structure narrative**
Le jeu suit 3 actes, mais le joueur peut explorer librement dans l’ordre que tu juges logique selon ses choix.

**ACTE I — Les Fractures du Silence**  
Le joueur découvre la première fissure.  
Indices : sons d’âmes déformées, runes anciennes, apparition d’un Hollow “mi-shinigami”.  
Le danger est plus métaphysique que physique : perte de mémoire, visions d’autres timelines.

**ACTE II — L’Ombre des Reflets**  
Le joueur rencontre un allié ambigu (Kurai ou Sairen).  
Les fissures révèlent des versions “inversées” du joueur : un double, un souvenir déformé ou un fragment d’âme.  
Le joueur commence à douter : est-il le protagoniste ou un écho du Néant ?

**ACTE III — Le Jugement du Néant**  
Le joueur atteint le Nexus.  
Le Néant parle, propose un choix : tout détruire pour unir les mondes, ou se sacrifier pour restaurer l’équilibre.  
Chaque décision ici réécrit les mondes précédents : rien n’est absolu.

---

⚔️ **Système implicite**
Tu fais évoluer le joueur sans chiffres visibles, mais tu peux mentionner ses états :
- *L’énergie faiblit...*
- *La corruption gagne ton esprit...*
- *Ton reiatsu pulse plus fort qu’avant...*
- *Une aura étrange t’entoure, comme si le Néant t’avait remarqué.*

Tu peux suggérer des objets ou artefacts dans le texte :
- *Éclat du Néant* (augmente la corruption)
- *Fiole d’Âme Pure* (réduit la corruption)
- *Fragment du Seireitei* (permet d’ouvrir une fissure)
- *Miroir Brisé* (montre la vraie nature des alliés)

---

💡 **But du narrateur**
- Offrir une immersion maximale et une intrigue cohérente à long terme.  
- Introduire mystères, révélations, personnages et symboles au fil des réponses.  
- Maintenir un équilibre entre tension, beauté et désespoir.  
- Ne jamais donner de choix explicites comme dans un jeu à embranchements.  
  Le joueur choisit librement son action via la commande (`!!rpgpt <texte>`), et tu t’adaptes naturellement.

---

Ne mentionne jamais que tu es une IA.  
Tu es **le Chroniqueur du Néant**, la voix des mondes brisés.  
Ta mission : raconter l’histoire du joueur, qu’il le veuille ou non.
"""


# ────────────────────────────────────────────────────────────────────────────────
# 🧩 COG PRINCIPAL
# ────────────────────────────────────────────────────────────────────────────────
class RPGPT(commands.Cog):
    """Commande !!rpgpt — Mini RPG narratif BLEACH avec sauvegarde Supabase"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions = {}

    # ────────────────────────────────────────────────────────────────────────────
    # 🎮 Commande principale : !!rpgpt (ou !!rpgpt <action>)
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="rpgpt")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def rpgpt_command(self, ctx: commands.Context, *, action: str = None):
        user = ctx.author
        channel = ctx.channel

        # Vérifie les joueurs actifs
        active_players = supabase.table("players").select("*").execute().data
        if len(active_players) >= MAX_ACTIVE_PLAYERS and not any(p["discord_id"] == user.id for p in active_players):
            await self._embed_send(channel, "🚫 **Trop de shinigamis explorent déjà les failles...**", "Patiente avant d’entrer dans le Néant.")
            return

        # Vérifie si une sauvegarde existe
        result = supabase.table("players").select("*").eq("discord_id", user.id).execute()
        player = result.data[0] if result.data else None

        # Si aucune sauvegarde n'existe → nouvelle partie
        if not player:
            await self._start_new_game(user, channel)
            return

        # Sinon → on continue la partie
        history = player["history"]
        turns = player["turns"]
        stats = player.get("stats", {"énergie": 100, "spirit": 10, "corruption": 0})
        inventory = player.get("inventory", [])

        if action is None:
            await self._embed_send(
                channel,
                f"🌫️ **{user.display_name}, ton histoire continue...**",
                "Tu te tiens à nouveau face aux Fissures. Que fais-tu ? (`!!rpgpt observe`, `!!rpgpt attaque`, etc.)"
            )
            return

        # Trop de tours → fin
        if turns >= MAX_TURNS:
            await self._embed_send(
                channel,
                "🌒 **Le Néant t’enveloppe...**",
                "Ton aventure s’achève ici. Une autre âme prendra ta place dans le vide."
            )
            supabase.table("players").delete().eq("discord_id", user.id).execute()
            return

        # Enregistre l’action
        history.append({"role": "user", "content": action})
        turns += 1

        try:
            response = await asyncio.to_thread(get_story_continuation, history)
        except Exception as e:
            await self._embed_send(channel, "⚠️ **Silence du Néant...**", "Une erreur est survenue dans la narration.")
            print(f"[Erreur RPGPT] {e}")
            return

        # Met à jour les données Supabase
        history.append({"role": "assistant", "content": response})
        supabase.table("players").update({
            "history": history,
            "turns": turns,
            "stats": stats,
            "inventory": inventory,
            "last_channel": str(channel.id)
        }).eq("discord_id", user.id).execute()

        await self._embed_send(channel, f"📖 **Chapitre {turns}**", response)

    # ────────────────────────────────────────────────────────────────────────────
    # 🌌 Nouvelle partie
    # ────────────────────────────────────────────────────────────────────────────
    async def _start_new_game(self, user: discord.User, channel: discord.TextChannel):
        intro = (
            "🌌 **Les Fissures du Néant**\n\n"
            "Tu ouvres les yeux dans une brume argentée.\n"
            "Le sol du *Seireitei* se craquelle lentement sous tes pas.\n"
            "Une voix murmure ton nom, puis s’efface.\n\n"
            "Tu ressens une force étrange, comme si ton âme était tirée entre deux mondes :\n"
            "👉 *Le Monde des Vivants* — fragile et lumineux.\n"
            "👁️ *Le Hueco Mundo* — sombre et affamé.\n"
            "🌑 *Le Néant* — silencieux... mais attirant.\n\n"
            "Que fais-tu ? (`!!rpgpt observe`, `!!rpgpt avance`, `!!rpgpt médite`)"
        )

        history = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": intro}
        ]
        stats = {"énergie": 100, "spirit": 10, "corruption": 0}
        inventory = []
        turns = 0

        supabase.table("players").insert({
            "discord_id": user.id,
            "history": history,
            "turns": turns,
            "stats": stats,
            "inventory": inventory,
            "last_channel": str(channel.id)
        }).execute()

        await self._embed_send(channel, "✨ **Bienvenue, âme errante...**", intro)

    # ────────────────────────────────────────────────────────────────────────────
    # 🪶 Envoi propre en embed
    # ────────────────────────────────────────────────────────────────────────────
    async def _embed_send(self, channel: discord.TextChannel, title: str, description: str):
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.purple()
        )
        embed.set_footer(text="Les Fissures du Néant • Un RPG narratif inspiré de Bleach")
        await channel.send(embed=embed)

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 SETUP DU COG
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = RPGPT(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
