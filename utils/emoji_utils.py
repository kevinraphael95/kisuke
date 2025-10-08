# utils/emoji_utils.py

emoji_code = {
    # ────────────── Python syntax ──────────────
    "🐍": "async def",
    "🏗️": "class",
    "🔙": "return",
    "⚡️": "await",
    "🟰": "if",
    "❌": "else",
    "🌀": "try",
    "🌪️": "except",
    "💨": "finally",
    "🔁": "for",
    "🔂": "while",
    "🔚": "break",
    "🔜": "continue",
    "🛑": "pass",

    # ────────────── Imports ──────────────
    "📌": "import",
    "📦": "from",

    # ────────────── Discord / Commands ──────────────
    "⚡c": "commands",
    "🐉": "discord",
    "🪄": "Bot",
    "📜": "Cog",
    "🧩": "@commands.command()",
    "⚡": "@app_commands.command",
    "🕐": "commands.cooldown",
    "⏱️": "commands.BucketType.user",

    # ────────────── Fonctions utilitaires internes ──────────────
    "🛡️": "safe_send",
    "🗑️": "safe_delete",
    "📝💬": "safe_respond",

    # ────────────── Discord objets ──────────────
    "🧊": "Embed",
    "🎨": "Color",
    "👀": "AllowedMentions",

    # ────────────── Variables / structures internes ──────────────
    "📝": "self",
    "🛠️": "bot",
    "📡": "channel",
    "💬": "message",
    "👤": "user",
    "🧃": "embed",
    "🧊": "embed_obj",

    # ────────────── Custom emojis / RegEx ──────────────
    "🗃️": "re",
    "🔎": "search",
    "🔧": "match",

    # ────────────── Booléens et valeurs simples ──────────────
    "✅": "True",
    "❎": "False",
    "🔢": "2000",

    # ────────────── Constantes texte ──────────────
    "💬🔁": '"Répéter le message"',
    "💌": '"✅ Message envoyé !"',
    "🔥": '"❌ Impossible d’envoyer le message."',

    # ────────────── Nombres en emojis ──────────────
    "0️⃣": "0",
    "1️⃣": "1",
    "2️⃣": "2",
    "3️⃣": "3",
    "4️⃣": "4",
    "5️⃣": "5",
    "6️⃣": "6",
    "7️⃣": "7",
    "8️⃣": "8",
    "9️⃣": "9",

    # ────────────── Commande classe spécifique ──────────────
    "💭": "SayEmoji",  # évite conflit avec 💬 utilisé dans les messages
}

def run_emoji_code(code_str, globals_dict):
    """Traduit les emojis du code en syntaxe Python et exécute."""
    for e, r in emoji_code.items():
        code_str = code_str.replace(e, r)
    exec(code_str, g
         lobals_dict)
