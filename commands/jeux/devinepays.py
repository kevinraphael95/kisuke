# ────────────────────────────────────────────────────────────────────────────────
# 📌 devinepays.py — Jeu /devinepays (inspiré CountryGuessr, version textuelle)
# Objectif : Deviner un pays aléatoire (bloc alphabétique de 10) en comparant caractéristiques
# Mode : Parties aléatoires par joueur (RAM), multi-essais, indices débloquables
# Commandes : /devinepays start <lettre>, /devinepays guess <pays>
#             !devinepays start <lettre>, !devinepays guess <pays>
# Catégorie : Jeux
# Accès : Tous
# Cooldown : 1 utilisation / 5 secondes / utilisateur
# ────────────────────────────────────────────────────────────────────────────────

import discord
from discord import app_commands
from discord.ext import commands
import aiohttp, random, math, asyncio, unicodedata, time

from utils.discord_utils import safe_send, safe_respond

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Config
# ────────────────────────────────────────────────────────────────────────────────
MAX_ATTEMPTS = 15
INDICE_FORMS_AT = 5
INDICE_BORDER_AT = 8
INDICE_CAPITAL_AT = 11

# seuils pour comparaison numérique (ratio)
CLOSE_RATIO = 0.10  # <10% -> proche (jaune)
FAR_RATIO = 0.40    # <40% -> éloigné (orange)
# sinon -> rouge (trop éloigné)

# traduction simple des continents anglais -> français
CONTINENT_TRANSLATE = {
    "Africa": "Afrique",
    "Americas": "Amériques",
    "Asia": "Asie",
    "Europe": "Europe",
    "Oceania": "Océanie",
    "Antarctic": "Antarctique",
    "": "Inconnu"
}

# ────────────────────────────────────────────────────────────────────────────────
# 🔧 Utilitaires
# ────────────────────────────────────────────────────────────────────────────────
def normalize(text: str) -> str:
    if text is None:
        return ""
    s = ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')
    return s.strip()

def haversine_km(coord1, coord2):
    """Distance (km) entre deux lat/lon"""
    try:
        lat1, lon1 = coord1
        lat2, lon2 = coord2
    except Exception:
        return 0
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return int(R * c)

def compare_numeric(a, b):
    """Retourne 'exact'|'close'|'far'|'wrong' et une flèche si pertinent"""
    if a is None or b is None:
        return "wrong", ""
    if a == b:
        return "exact", ""
    diff = abs(a - b)
    ratio = diff / max(a, b) if max(a, b) > 0 else 1.0
    if ratio < CLOSE_RATIO:
        arrow = "⬆️" if a < b else "⬇️"
        return "close", arrow
    if ratio < FAR_RATIO:
        arrow = "⬆️" if a < b else "⬇️"
        return "far", arrow
    return "wrong", "⬆️" if a < b else "⬇️"

def color_emoji(code: str) -> str:
    return {"exact": "🟩", "close": "🟨", "far": "🟧", "wrong": "🟥"}.get(code, "🟥")

# ────────────────────────────────────────────────────────────────────────────────
# 🗂️ Cog : DevinePays
# ────────────────────────────────────────────────────────────────────────────────
class DevinePays(commands.Cog):
    """Jeu /devinepays et !devinepays — Devine un pays à partir de comparaisons (bloc alphabétique 10)"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.countries = []          # liste de dicts (chargée depuis restcountries)
        self.name_to_country = {}    # mapping normalized_name -> country dict
        self.games = {}              # parties en cours : user_id -> game dict

    # ────────────────────────────────────────────────────────────────────────────
    # Chargement des données au démarrage du cog
    # ────────────────────────────────────────────────────────────────────────────
    async def cog_load(self):
        await self._load_countries()

    async def _load_countries(self):
        url = "https://restcountries.com/v3.1/all"
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as r:
                data = await r.json()
        parsed = []
        for c in data:
            try:
                name = c.get("name", {}).get("common")
                if not name:
                    continue
                # population, area, region, languages, currencies, borders, latlng, capital
                population = c.get("population", 0)
                area = int(c.get("area", 0)) if c.get("area") is not None else 0
                region = c.get("region", "")  # continent
                languages = list(c.get("languages", {}).values()) if c.get("languages") else []
                currencies = list(c.get("currencies", {}).keys()) if c.get("currencies") else []
                currency = currencies[0] if currencies else "?"
                borders = c.get("borders", []) or []
                borders_count = len(borders)
                latlng = c.get("latlng", None) or [0, 0]
                capital_list = c.get("capital", []) or []
                capital = capital_list[0] if capital_list else ""
                flags = c.get("flags", {}) or {}
                flag_png = flags.get("png") if isinstance(flags, dict) else None
                parsed.append({
                    "name": name,
                    "normalized": normalize(name),
                    "continent": region,
                    "languages": languages,
                    "population": population,
                    "currency": currency,
                    "borders": borders_count,
                    "borders_list": borders,
                    "area": area,
                    "latlng": latlng,
                    "capital": capital,
                    "flag_png": flag_png
                })
            except Exception:
                continue
        # tri alphabétique par nom
        parsed.sort(key=lambda x: x["name"])
        self.countries = parsed
        self.name_to_country = {c["normalized"]: c for c in parsed}
        # ready
        print(f"[devinepays] Chargé {len(self.countries)} pays depuis restcountries")

    # ────────────────────────────────────────────────────────────────────────────
    # Helpers : blocs alphabétiques de 10
    # ────────────────────────────────────────────────────────────────────────────
    def get_block_by_letter(self, letter: str):
        """Retourne un bloc de 10 pays commençant (ou démarrant) à partir de la lettre donnée."""
        if not self.countries:
            return []
        letter = letter[0].upper() if letter else "A"
        # find first index whose name starts with letter or with next letter if none
        start_idx = None
        for i, c in enumerate(self.countries):
            if c["name"].upper().startswith(letter):
                start_idx = i
                break
        if start_idx is None:
            # fallback : find first country whose first letter >= letter
            for i, c in enumerate(self.countries):
                if c["name"][0].upper() >= letter:
                    start_idx = i
                    break
        if start_idx is None:
            start_idx = 0
        # slice 10, wrap if needed
        end_idx = start_idx + 10
        block = []
        idx = start_idx
        while len(block) < 10:
            block.append(self.countries[idx % len(self.countries)])
            idx += 1
            if idx - start_idx >= len(self.countries):
                break
        return block

    # ────────────────────────────────────────────────────────────────────────────
    # Commandes SLASH
    # ────────────────────────────────────────────────────────────────────────────
    @app_commands.command(name="devinepays", description="Démarrer ou jouer au quiz DevinePays")
    @app_commands.describe(action="start pour démarrer une partie, guess pour tenter un pays", lettre="Lettre de départ pour start (A–Z)", pays="Nom du pays pour guess")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: i.user.id)
    async def slash_devinepays(self, interaction: discord.Interaction, action: str, lettre: str = None, pays: str = None):
        # On gère deux actions : start / guess
        action = (action or "").lower()
        try:
            if action == "start":
                lettre = (lettre or "A").strip().upper()[0]
                await interaction.response.defer()
                await self._start_game(interaction, lettre)
                return
            elif action == "guess":
                if not pays:
                    await safe_respond(interaction, "❌ Utilisation : `/devinepays guess <nom_du_pays>`.", ephemeral=True)
                    return
                await interaction.response.defer()
                await self._handle_guess(interaction.user, interaction.channel, pays, interaction)
                return
            else:
                await safe_respond(interaction, "❌ Action inconnue. Utilise 'start' ou 'guess'.", ephemeral=True)
        except Exception as e:
            print(f"[ERREUR /devinepays] {e}")
            await safe_respond(interaction, "❌ Une erreur est survenue.", ephemeral=True)

    # ────────────────────────────────────────────────────────────────────────────
    # Commandes PREFIX
    # ────────────────────────────────────────────────────────────────────────────
    @commands.command(name="devinepays")
    @commands.cooldown(1, 5.0, commands.BucketType.user)
    async def prefix_devinepays(self, ctx: commands.Context, action: str = None, arg: str = None):
        """Usage : !devinepays start <lettre>   ou   !devinepays guess <pays>"""
        action = (action or "").lower()
        try:
            if action == "start":
                lettre = (arg or "A").strip().upper()[0]
                await self._start_game(ctx, lettre)
                return
            elif action == "guess":
                if arg is None:
                    await safe_send(ctx.channel, "❌ Utilisation : `!devinepays guess <nom_du_pays>`.")
                    return
                await self._handle_guess(ctx.author, ctx.channel, arg, ctx)
                return
            else:
                await safe_send(ctx.channel, "❌ Action inconnue. Utilise `start` ou `guess`.")
        except Exception as e:
            print(f"[ERREUR !devinepays] {e}")
            await safe_send(ctx.channel, "❌ Une erreur est survenue.")

    # ────────────────────────────────────────────────────────────────────────────
    # Démarrage d'une partie
    # ────────────────────────────────────────────────────────────────────────────
    async def _start_game(self, source, lettre: str):
        """source : interaction OR ctx"""
        if isinstance(source, discord.Interaction):
            channel = source.channel
            user = source.user
        else:
            channel = source.channel
            user = source.author

        block = self.get_block_by_letter(lettre)
        if not block:
            await safe_send(channel, f"❌ Aucun pays trouvé pour la lettre **{lettre}**.")
            return

        secret = random.choice(block)
        # stock de la partie
        self.games[user.id] = {
            "secret": secret,
            "block": block,
            "guesses": [],           # liste de noms devinés (normalisé)
            "start_time": time.time(),
            "ended": False
        }

        names_range = f"{block[0]['name']} — {block[-1]['name']}"
        embed = discord.Embed(
            title="🌍 DevinePays — Partie démarrée",
            description=f"J'ai choisi un pays aléatoire **dans le bloc** : **{names_range}**.\nFais une tentative avec ` /devinepays guess <nom_du_pays>` ou `!devinepays guess <nom_du_pays>`.\nTu as **{MAX_ATTEMPTS}** essais maximum.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Bloc démarré par : {user.display_name}")
        await safe_send(channel, embed=embed)

    # ────────────────────────────────────────────────────────────────────────────
    # Gestion d'un guess
    # ────────────────────────────────────────────────────────────────────────────
    async def _handle_guess(self, user, channel, guess_raw: str, ctx_or_interaction):
        uid = user.id
        game = self.games.get(uid)
        if not game or game.get("ended"):
            await safe_respond(ctx_or_interaction, "❌ Tu n'as pas de partie en cours. Lance-en une avec `start <lettre>`.", ephemeral=True)
            return

        guess_name = guess_raw.strip()
        normalized_guess = normalize(guess_name)
        # trouver le pays correspondant (supporte approximations via mapping exact only)
        target_country = self.name_to_country.get(normalized_guess)
        if not target_country:
            # try to match by ignoring accents and some punctuation already done by normalize
            # alternative: search for country whose normalized contains the guess as substring
            found = None
            for c in self.countries:
                if normalized_guess == c["normalized"]:
                    found = c
                    break
                if normalized_guess in c["normalized"]:
                    found = c
                    break
            if found:
                target_country = found
        if not target_country:
            await safe_respond(ctx_or_interaction, "❌ Pays introuvable ou mal orthographié. Assure-toi d'utiliser le nom courant (ex: France, Brésil).", ephemeral=True)
            return

        # enregistrer l'essai
        game["guesses"].append(target_country["normalized"])

        # comparer
        secret = game["secret"]
        embed = await self._build_comparison_embed(target_country, secret, user, len(game["guesses"]))
        await safe_send(channel, embed=embed)

        # check win
        if target_country["normalized"] == secret["normalized"]:
            # gagné
            game["ended"] = True
            await safe_send(channel, f"🎉 Félicitations {user.mention} — tu as trouvé le pays mystère **{secret['name']}** en {len(game['guesses'])} essai(s) !")
            # cleanup after short delay
            await asyncio.sleep(0.1)
            del self.games[uid]
            return

        # check attempts exceeded
        if len(game["guesses"]) >= MAX_ATTEMPTS:
            game["ended"] = True
            await safe_send(channel, f"❌ Tu as atteint {MAX_ATTEMPTS} essais. Le pays mystère était **{secret['name']}**.")
            del self.games[uid]
            return

        # Indices débloquables
        await self._maybe_send_indices(channel, game, user)

    # ────────────────────────────────────────────────────────────────────────────
    # Construction de l'embed comparatif
    # ────────────────────────────────────────────────────────────────────────────
    async def _build_comparison_embed(self, guess, secret, player, attempt_number: int):
        # continent
        cont_guess = CONTINENT_TRANSLATE.get(guess.get("continent", ""), guess.get("continent", "") or "Inconnu")
        cont_secret = CONTINENT_TRANSLATE.get(secret.get("continent", ""), secret.get("continent", "") or "Inconnu")
        cont_color = "exact" if guess.get("continent") == secret.get("continent") else "wrong"

        # languages -> exact if any language matches; show list (first 3)
        guess_langs = guess.get("languages", []) or []
        secret_langs = secret.get("languages", []) or []
        lang_match = any(normalize(l) in [normalize(s) for s in secret_langs] for l in guess_langs)
        lang_color = "exact" if lang_match else "wrong"

        # population
        pop_guess = guess.get("population", 0)
        pop_secret = secret.get("population", 0)
        pop_cmp, pop_arrow = compare_numeric(pop_guess, pop_secret)

        # currency
        cur_guess = guess.get("currency", "?")
        cur_secret = secret.get("currency", "?")
        cur_color = "exact" if cur_guess == cur_secret else "wrong"

        # borders count
        bord_guess = guess.get("borders", 0)
        bord_secret = secret.get("borders", 0)
        bord_cmp, bord_arrow = compare_numeric(bord_guess, bord_secret)

        # area
        area_guess = guess.get("area", 0)
        area_secret = secret.get("area", 0)
        area_cmp, area_arrow = compare_numeric(area_guess, area_secret)

        # distance between centroids (latlng)
        dist_km = haversine_km(guess.get("latlng", [0,0]), secret.get("latlng", [0,0]))
        # For distance comparison we evaluate relative to half Earth's circumference (~20037 km)
        # We'll compare to secret distance 0: smaller = close -> use same compare_numeric but between dist and 0
        # Instead, classify distance by absolute thresholds relative to Earth's half-circumference:
        max_dist = 20037  # approx half circ
        ratio = dist_km / max_dist
        if dist_km == 0:
            dist_code = "exact"
        elif ratio < 0.10:
            dist_code = "close"
        elif ratio < 0.40:
            dist_code = "far"
        else:
            dist_code = "wrong"

        # build embed
        title = f"🧩 Essai #{attempt_number} — {guess['name']}"
        embed = discord.Embed(title=title, color=discord.Color.blurple())
        embed.add_field(name="🌍 Continent", value=f"{color_emoji(cont_color)} {cont_guess} — (Cible: {cont_secret})", inline=False)
        embed.add_field(name="🗣️ Langues", value=f"{color_emoji(lang_color)} {', '.join(guess_langs) if guess_langs else '—'}", inline=False)
        embed.add_field(name="👥 Population", value=f"{color_emoji(pop_cmp)} {pop_guess:,} {pop_arrow} — (Cible: {pop_secret:,})", inline=False)
        embed.add_field(name="💰 Monnaie (code)", value=f"{color_emoji(cur_color)} {cur_guess} — (Cible: {cur_secret})", inline=False)
        embed.add_field(name="🚧 Nombre de frontières", value=f"{color_emoji(bord_cmp)} {bord_guess} {bord_arrow} — (Cible: {bord_secret})", inline=False)
        embed.add_field(name="📏 Superficie (km²)", value=f"{color_emoji(area_cmp)} {area_guess:,} {area_arrow} — (Cible: {area_secret:,})", inline=False)
        embed.add_field(name="📍 Distance (km)", value=f"{color_emoji(dist_code)} {dist_km:,} km", inline=False)

        # small footer with player
        embed.set_footer(text=f"Joueur : {player.display_name}")
        return embed

    # ────────────────────────────────────────────────────────────────────────────
    # Indices débloqués selon nombre d'essais
    # ────────────────────────────────────────────────────────────────────────────
    async def _maybe_send_indices(self, channel, game, user):
        n = len(game["guesses"])
        secret = game["secret"]

        # forme (on utilise le drapeau comme proxy de "forme" si disponible)
        if n >= INDICE_FORMS_AT and not game.get("indice_forme_sent"):
            game["indice_forme_sent"] = True
            if secret.get("flag_png"):
                embed = discord.Embed(title="🔎 Indice — Forme (proxy : drapeau)", description="Voici un indice visuel (drapeau) pour t'aider.", color=discord.Color.gold())
                embed.set_image(url=secret["flag_png"])
                await safe_send(channel, embed=embed)
            else:
                await safe_send(channel, "🔎 Indice — Forme : (aucune image disponible pour ce pays)")

        # pays frontalier (ou plus proche si aucun frontalier)
        if n >= INDICE_BORDER_AT and not game.get("indice_border_sent"):
            game["indice_border_sent"] = True
            borders_codes = secret.get("borders_list", []) or []
            if borders_codes:
                # restcountries uses cca3 codes (ISO3). Map codes -> names by searching countries loaded.
                neighbor = None
                for code in borders_codes:
                    for c in self.countries:
                        # we don't have cca3 stored; but restcountries 'borders' list contains cca3 codes: let's try to match by currency? fallback: show code
                        # Best effort: check if any country's name normalized includes code (unlikely). So we will lookup via an extra mapping if available.
                        pass
                # simpler approach: take first border code and display code (users understand)
                await safe_send(channel, f"🔎 Indice — Pays frontalier : code ISO3 **{borders_codes[0]}** (frontalier du pays mystère).")
            else:
                # aucun frontalier -> on donne le pays le plus proche géographiquement
                closest = None
                min_d = None
                for c in self.countries:
                    if c["normalized"] == secret["normalized"]:
                        continue
                    d = haversine_km(c.get("latlng", [0,0]), secret.get("latlng", [0,0]))
                    if min_d is None or d < min_d:
                        min_d = d
                        closest = c
                if closest:
                    await safe_send(channel, f"🔎 Indice — Pays frontalier (ou plus proche) : **{closest['name']}**")
                else:
                    await safe_send(channel, "🔎 Indice — Aucun pays frontalier disponible / calcul impossible.")

        # capitale
        if n >= INDICE_CAPITAL_AT and not game.get("indice_cap_sent"):
            game["indice_cap_sent"] = True
            cap = secret.get("capital")
            if cap:
                await safe_send(channel, f"🔎 Indice — Capitale : **{cap}**")
            else:
                await safe_send(channel, "🔎 Indice — Capitale : (inconnue)")

    # ────────────────────────────────────────────────────────────────────────────
    # Cleanup on cog unload
    # ────────────────────────────────────────────────────────────────────────────
    async def cog_unload(self):
        self.games.clear()

# ────────────────────────────────────────────────────────────────────────────────
# 🔌 Setup du Cog
# ────────────────────────────────────────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = DevinePays(bot)
    for command in cog.get_commands():
        if not hasattr(command, "category"):
            command.category = "Jeux"
    await bot.add_cog(cog)
