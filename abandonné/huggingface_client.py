# ────────────────────────────────────────────────────────────────────────────────
# 📌 huggingface_client.py — Gestion des appels à l'API Hugging Face
# Objectif : Fournir une fonction get_story_continuation() pour le mini-RPG
# avec fallback automatique entre plusieurs modèles gratuits
# ────────────────────────────────────────────────────────────────────────────────

import os
import requests

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Configuration
# ────────────────────────────────────────────────────────────────────────────────
HF_API_KEY = os.getenv("HF_API_KEY")
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

# Liste de modèles gratuits légers et accessibles
MODEL_URLS = [
    "https://api-inference.huggingface.co/models/TheBloke/gpt4all-lora-quantized",
    "https://api-inference.huggingface.co/models/TheBloke/GPT4-x-Alpaca-7B-Chat",
    "https://api-inference.huggingface.co/models/mosaicml/mpt-7b-chat",
]

print("🔑 Clé HuggingFace détectée :", bool(HF_API_KEY))

# ────────────────────────────────────────────────────────────────────────────────
# 💬 Fonction principale — génération du texte narratif
# ────────────────────────────────────────────────────────────────────────────────
def get_story_continuation(history: list[dict]) -> str:
    """
    Génère la suite du scénario à partir de l'historique.
    Chaque élément de 'history' est une dict : {role: 'user'/'assistant'/'system', content: str}
    """

    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in history]) + "\nassistant:"

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.9,
            "repetition_penalty": 1.1,
        }
    }

    for url in MODEL_URLS:
        try:
            response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
            if response.status_code != 200:
                print(f"[Erreur HF] Modèle {url} → {response.status_code}: {response.text}")
                continue

            data = response.json()
            if isinstance(data, list):
                text = data[0].get("generated_text", "")
            elif "generated_text" in data:
                text = data["generated_text"]
            else:
                text = str(data)

            text = text.split("assistant:")[-1].strip()
            if text:
                return text
        except Exception as e:
            print(f"[Erreur HF] Modèle {url} → {e}")
            continue

    # Si aucun modèle ne répond
    return "⚠️ Le narrateur reste silencieux... (*tous les modèles ont échoué*)"
