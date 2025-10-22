# ────────────────────────────────────────────────────────────────────────────────
# 📌 gpt_oss_client.py — Connexion cloud NVIDIA GPT-OSS (pour !!gpt)
# ────────────────────────────────────────────────────────────────────────────────
import os
from openai import OpenAI
import requests

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
def get_simple_response(prompt: str, max_response_chars: int = 90) -> str:
    """
    Envoie un prompt texte à GPT-OSS NVIDIA (cloud) et renvoie la réponse directe.
    Limite la réponse à `max_response_chars` caractères.
    """
    try:
        # Ajout d'une consigne explicite dans le prompt pour guider la longueur
        full_prompt = f"{prompt}\nRéponds en français et fais une réponse concise, max {max_response_chars} caractères."

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "Tu es un assistant conversationnel précis, immersif et bienveillant."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.8,
            top_p=0.7,
            max_tokens=512
        )
        text = response.choices[0].message.content.strip()

        # Sécurité : tronquer si le modèle dépasse encore la limite
        if len(text) > max_response_chars:
            text = text[:max_response_chars]
        return text

    except Exception as e:
        print(f"[Erreur GPT-OSS Simple] {type(e)} — {e}")
        return "⚠️ Le modèle est silencieux pour le moment..."

# ────────────────────────────────────────────────────────────────────────────────
# Fonction pour récupérer le quota restant
# ────────────────────────────────────────────────────────────────────────────────
def remaining_tokens() -> int:
    """
    Retourne le nombre de tokens restants dans le quota mensuel NVIDIA GPT-OSS.
    Approximation : 100 000 tokens par mois (free-tier)
    """
    try:
        resp = requests.get(
            f"{BASE_URL}/usage",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()
        used = data.get("token_used", 0)
        quota = data.get("token_quota", 100_000)
        return quota - used
    except Exception as e:
        print(f"[Erreur remaining_tokens] {e}")
        return 100_000
