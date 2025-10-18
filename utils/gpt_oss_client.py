# ────────────────────────────────────────────────────────────────────────────────
# 📌 gpt_oss_client.py — Gestion des appels à l'API GPT-OSS (NVIDIA) gratuite
# ────────────────────────────────────────────────────────────────────────────────
import os
from openai import OpenAI

# ────────────────────────────────────────────────────────────────────────────────
# 🔑 Clé NVIDIA gratuite
# Stockée dans l'environnement : GPT_OSS_API_KEY
API_KEY = os.getenv("GPT_OSS_API_KEY")
BASE_URL = "https://integrate.api.nvidia.com/v1"

print("🔑 Clé GPT-OSS NVIDIA détectée :", bool(API_KEY))

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Initialisation du client
client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# ────────────────────────────────────────────────────────────────────────────────
# 💬 Fonction principale — génération du texte narratif
def get_story_continuation(history: list[dict]) -> str:
    """
    Envoie l'historique du RPG à GPT-OSS NVIDIA et renvoie la suite de l'histoire.
    Chaque élément de 'history' est une dict : {role: 'user'/'assistant'/'system', content: str}
    """
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=history,
            temperature=0.95,
            top_p=0.7,
            max_tokens=1024
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Erreur GPT-OSS] {e}")
        return "⚠️ Le narrateur se tait... (*erreur du modèle*)"
