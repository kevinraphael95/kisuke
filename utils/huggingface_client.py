# ────────────────────────────────────────────────────────────────────────────────
# 📌 huggingface_client.py — Gestion des appels à l'API Hugging Face
# Objectif : Fournir une fonction get_story_continuation() pour le mini-RPG
# ────────────────────────────────────────────────────────────────────────────────

import os
import requests

# ────────────────────────────────────────────────────────────────────────────────
# ⚙️ Configuration du modèle
# ────────────────────────────────────────────────────────────────────────────────
HF_API_KEY = os.getenv("HF_API_KEY")
MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

print("🔑 Clé HuggingFace détectée :", bool(HF_API_KEY))

# ────────────────────────────────────────────────────────────────────────────────
# 💬 Fonction principale — génération du texte narratif
# ────────────────────────────────────────────────────────────────────────────────
def get_story_continuation(history: list[dict]) -> str:
    """
    Génère la suite du scénario à partir de l'historique.
    Chaque élément de 'history' est une dict : {role: 'user'/'assistant'/'system', content: str}
    """

    # On recompose le prompt complet à partir de l'historique
    prompt = "\n".join([f"{m['role']}: {m['content']}" for m in history])
    payload = {
        "inputs": f"{prompt}\nassistant:",
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.9,
            "repetition_penalty": 1.1,
        }
    }

    try:
        response = requests.post(MODEL_URL, headers=HEADERS, json=payload, timeout=60)

        if response.status_code != 200:
            print(f"[Erreur HuggingFace] {response.status_code}: {response.text}")
            return "⚠️ Le narrateur reste silencieux... (*erreur du modèle*)"

        data = response.json()
        # HuggingFace peut renvoyer plusieurs formats différents selon le modèle
        if isinstance(data, list):
            text = data[0].get("generated_text", "")
        elif "generated_text" in data:
            text = data["generated_text"]
        else:
            text = str(data)

        # Nettoyage basique du texte
        text = text.split("assistant:")[-1].strip()
        return text or "🌫️ Le Néant murmure sans mot..."

    except Exception as e:
        print(f"[Erreur HF API] {e}")
        return "⚠️ Le narrateur se tait... (*erreur de connexion*)"
