# 📦 Installation & Configuration du bot Discord avec Render + Supabase + Self-Ping

---

## 🚀 Outils utilisés

* **[Supabase](https://supabase.com/)** → Base de données SQL gratuite
* **[Render](https://render.com/)** → Hébergement gratuit du bot
* **Self-ping** → Pour que le bot reste actif (optionnel : UptimeRobot)

---

## 1️⃣ Créer et configurer ton application Discord

1. Va sur [Discord Developer Portal](https://discord.com/developers/applications)
2. Clique sur **New Application** → nomme ton application
3. Dans **General Information**, note ton **APPLICATION ID** → tu en auras besoin pour le `.env`
4. Va dans **Bot → Reset Token** → copie le **BOT TOKEN** → tu en auras besoin pour le `.env`

> ✅ Ces deux infos servent à connecter ton bot à Discord.

---

## 2️⃣ Configurer Supabase

1. Crée un projet sur [Supabase](https://supabase.com/)
2. Crée les tables via les script SQL
3. Note les informations suivantes pour le `.env` :

   * **SUPABASE_URL** → `Project Settings → Data API → Project URL`
   * **SUPABASE_KEY** → `Project Settings → API Keys → Publishable Keys ou Secret Keys`
   

> ✅ Ces deux infos permettent au bot de lire/écrire dans ta base de données.

---

## 3️⃣ Créer le webhook de redeploy Render

1. Connecte-toi à [Render](https://render.com/) → ton service (bot)
2. **Settings → Build & Deploy → Deploy Hooks → Create Deploy Hook**
3. Copie l’URL générée → ce sera ton **RENDER_REDEPLOY_WEBHOOK** dans le `.env`

> ✅ Ce webhook permet de redéployer ton bot depuis Discord via une commande, sans toucher à Render.

---

## 4️⃣ Préparer ton fichier `.env`

Maintenant que tu as toutes les infos, crée un fichier `.env` **à la racine du projet** :

```env
# --- Discord ---
COMMAND_PREFIX=!!
DISCORD_APP_ID=TON_APPLICATION_ID  # depuis Discord Developer Portal
DISCORD_TOKEN=TON_BOT_TOKEN        # depuis Discord Developer Portal

# --- Supabase ---
SUPABASE_URL=TON_URL_SUPABASE      # depuis Supabase
SUPABASE_KEY=TA_CLE_API_SUPABASE   # depuis Supabase

# --- Render ---
PING_URL=https://ton-bot.onrender.com/   # URL publique du bot Render
RENDER_REDEPLOY_WEBHOOK=https://api.render.com/deploy/srv-xxxxxx?key=yyyyyyyy
```

> ⚡ **Explications :**
>
> * `COMMAND_PREFIX` → préfixe utilisé pour tes commandes Discord (`!`, `!!`, etc.)
> * `DISCORD_APP_ID` et `DISCORD_TOKEN` → connectent ton bot à Discord
> * `SUPABASE_URL` et `SUPABASE_KEY` → connectent ton bot à la base de données
> * `PING_URL` → permet au bot de se ping lui-même pour rester actif
> * `RENDER_REDEPLOY_WEBHOOK` → permet de redéployer le bot via une commande

---

## 5️⃣ Déployer sur Render

1. Render → **New → Web Service** → sélectionne ton dépôt GitHub
2. Choisis le **plan gratuit**
3. **Startup Command** :

```bash
python bot.py
```

4. Dans **Environment Variables**, ajoute **toutes les valeurs du `.env`**
5. Advanced → Auto Deploy → **OFF**

---

## 6️⃣ Maintenir le bot actif (self-ping)

Crée un fichier `keep_alive.py` :

```python
from flask import Flask
import threading, requests, time, os

app = Flask('')

@app.route('/')
def home():
    return "✅ Bot en ligne"

def run():
    app.run(host='0.0.0.0', port=8080)

def ping_self():
    while True:
        try: requests.get(os.getenv("PING_URL"))
        except: pass
        time.sleep(300)

threading.Thread(target=run).start()
threading.Thread(target=ping_self).start()
```

Dans `bot.py` :

```python
from tasks.keep_alive import keep_alive
keep_alive()
```

> 🔹 Le bot se ping tout seul → Render ne le met jamais en veille.

---

## 7️⃣ (Optionnel) UptimeRobot

* Crée un monitor HTTP(s) → URL = `PING_URL`
* Intervalle = 5 minutes
* Sert de ping externe si tu veux

---

## 8️⃣ Redéploiement depuis Discord

Dans ton code, tu peux créer une commande `!re` :

```python
import os, requests

def redeploy():
    webhook = os.getenv("RENDER_REDEPLOY_WEBHOOK")
    if webhook:
        requests.post(webhook)
        print("♻️ Redéploiement lancé !")
```

> ⚡ La commande appelle le webhook et Render redéploie ton bot automatiquement.

