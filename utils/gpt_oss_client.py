# ────────────────────────────────────────────────────────────────────────────────
# 📌 gpt_oss_client.py — Connexion cloud NVIDIA GPT-OSS (pour !!gpt et /rpgpt)
# ────────────────────────────────────────────────────────────────────────────────
import os
from openai import OpenAI

# ────────────────────────────────────────────────────────────────────────────────
# 🔑 Clé NVIDIA (cloud)
# ────────────────────────────────────────────────────────────────────────────────
API_KEY = os.getenv("GPT_OSS_API_KEY")
BASE_URL = "https://integrate.api.nvidia.com/v1"

if not API_KEY:
    print("❌ Aucune clé GPT-OSS détectée. Configure GPT_OSS_API_KEY dans ton environnement.")
else:
    print("✅ Clé NVIDIA GPT-OSS détectée — utilisation du cloud.")

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Initialisation du client NVIDIA Cloud
# ────────────────────────────────────────────────────────────────────────────────
client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# ────────────────────────────────────────────────────────────────────────────────
# 💬 Réponse simple (commande !!gpt)
# ────────────────────────────────────────────────────────────────────────────────
def get_simple_response(prompt: str) -> str:
    """
    Envoie un simple prompt texte à GPT-OSS NVIDIA (cloud) et renvoie la réponse directe.
    Utilisé pour la commande !!gpt.
    """
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "Tu es un assistant conversationnel précis, immersif et bienveillant. Réponds toujours en français."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            top_p=0.7,
            max_tokens=512
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Erreur GPT-OSS Simple] {type(e)} — {e}")
        return "⚠️ Le modèle est silencieux pour le moment..."

# ────────────────────────────────────────────────────────────────────────────────
# 💬 Continuation d’histoire (utilisée par RPGPT)
# ────────────────────────────────────────────────────────────────────────────────
def get_story_continuation(history: list[dict]) -> str:
    """
    Envoie l'historique du RPG à GPT-OSS NVIDIA (cloud) et renvoie la suite de l'histoire.
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
        print(f"[Erreur GPT-OSS Histoire] {type(e)} — {e}")
        return "⚠️ Le narrateur se tait... (*erreur du modèle ou limite atteinte*)"
