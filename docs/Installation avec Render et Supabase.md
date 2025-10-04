# Installer avec Render, Supabase et Self-Ping

---

## 1️⃣ Discord

1. [Discord Developer Portal](https://discord.com/developers/applications) → **New Application**
2. Note **APPLICATION ID**
3. Bot → **Reset Token** → copie **BOT TOKEN**

> Ces deux infos vont dans le `.env`.

---

## 2️⃣ Supabase

1. Crée un projet sur [Supabase](https://supabase.com/)
2. Crée les tables via le script SQL
3. Note pour le `.env` :

   * `SUPABASE_URL` → Project URL
   * `SUPABASE_KEY` → Service Role Key

---

## 3️⃣ Webhook de redeploy Render

1. Render → ton service → **Settings → Build & Deploy → Deploy Hooks → Create Deploy Hook**
2. Copie l’URL → ce sera `RENDER_REDEPLOY_WEBHOOK` dans le `.env`

> Permet de redéployer le bot depuis Discord.

---

## 4️⃣ Fichier `.env`

```env
# --- Discord ---
COMMAND_PREFIX=!!
DISCORD_APP_ID=TON_APPLICATION_ID
DISCORD_TOKEN=TON_BOT_TOKEN

# --- Supabase ---
SUPABASE_URL=TON_URL_SUPABASE
SUPABASE_KEY=TA_CLE_API_SUPABASE

# --- Render ---
PING_URL=https://ton-bot.onrender.com/
RENDER_REDEPLOY_WEBHOOK=https://api.render.com/deploy/srv-xxxxxx?key=yyyyyyyy
```

> **Explications** :
>
> * `COMMAND_PREFIX` → préfixe des commandes (`!`, `!!`)
> * `DISCORD_APP_ID` / `DISCORD_TOKEN` → connexion Discord
> * `SUPABASE_URL` / `SUPABASE_KEY` → connexion base de données
> * `PING_URL` → self-ping pour rester actif
> * `RENDER_REDEPLOY_WEBHOOK` → redeploy depuis Discord

---

## 5️⃣ Déployer sur Render

1. Render → **New → Web Service** → dépôt GitHub
2. Plan gratuit
3. Startup command : `python bot.py`
4. Environment Variables → copie **toutes les valeurs du `.env`**
5. Advanced → Auto Deploy → **OFF**

---

## 6️⃣ Self-Ping (keep_alive.py)

```python
from flask import Flask
import threading, requests, time, os

app = Flask('')

@app.route('/')
def home(): return "✅ Bot en ligne"

def run(): app.run(host='0.0.0.0', port=8080)

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

> Le bot se ping tout seul → jamais en veille.

---

## 7️⃣ Redéploiement depuis Discord

```python
import os, requests

def redeploy():
    webhook = os.getenv("RENDER_REDEPLOY_WEBHOOK")
    if webhook: requests.post(webhook)
```

* Crée une commande `!re` → le bot redéploie automatiquement via Render.

