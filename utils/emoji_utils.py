# emoji_utils.py
emoji_code = {
    # mots-clés Python
    "🐍": "async def",
    "🏗️": "class",
    "🔙": "return",
    "⚡️": "await",
    "🟰": "if",
    "❌": "else",
    "🌀": "try",
    "🌪️": "except",
    "💨": "finally",
    "➕": "+",
    "➖": "-",
    "✖️": "*",
    "➗": "/",
    "🔁": "for",
    "🔂": "while",
    "🔚": "break",
    "🔜": "continue",
    "🛑": "pass",
    "📌": "import",
    "📦": "from",
    "🧩": "@commands.command()",
    "⚡": "@app_commands.command(",

    # modules / classes
    "🐉": "discord",
    "⚡c": "commands",
    "🪄": "Bot",
    "📜": "Cog",
    "🧊": "Embed",
    "📢": "send",
    "👀": "AllowedMentions",
    "🖼️": "color",
    "🎨": "Color",
    "💥": "Exception",
    "🔧": "match",
    "🔎": "search",
    "🗃️": "re",

    # bot utils
    "🛡️": "safe_send",
    "🗑️": "safe_delete",
    "📝💬": "safe_respond",

    # variables
    "📝": "self",
    "📡": "channel",
    "👤": "user",
    "💬": "message",
    "🧃": "embed",
    "🧊": "embed_obj",
    "🕵️‍♂️": "parse_options",
    "🎭": "replace_custom_emojis",
    "🕐": "command",
    "🛠️": "bot",
    "🔢": "2000",

    # nombres 0-9
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

    # booléens
    "✅": "True",
    "❎": "False",

    # chaînes communes
    "💌": '"Message envoyé !"',
    "🔥": '"Impossible d’envoyer le message."',
    "💬🔁": '"Répéter le message"',
    "⚠️": '"Erreur"',
    
    # emojis utiles pour décorateurs et options
    "📝✨": "ephemeral=True",
    "⏱️": "commands.BucketType.user",
    "⏰": "5",
}

def run_emoji_code(code_str, globals_dict):
    for e, r in emoji_code.items():
        code_str = code_str.replace(e, r)
    exec(code_str, globals_dict)
