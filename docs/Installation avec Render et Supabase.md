# 📦 Installation & Configuration avec Render, Supabase et Self-Ping (plus Uptime Robot en option)

---

## 🚀 Outils utilisés

* **[Supabase](https://supabase.com/)** : Base de données SQL gratuite
* **[Render](https://render.com/)** : Hébergeur gratuit pour le bot
* **[UptimeRobot](https://uptimerobot.com/)** : Optionnel pour pinger le bot et le maintenir actif si vous ne voulez pas utiliser le self-ping

---

### 1️⃣ Créer et configurer l’application Discord

1. Se connecter au [Portail Développeur Discord](https://discord.com/developers/applications)
2. **Créer une nouvelle application**
3. Dans **General Information** :

   * Noter l’`APPLICATION ID` (utile pour certaines fonctions ou logs)
4. Aller dans l’onglet **Bot** :

   * Cliquer sur **Reset Token** pour obtenir le **Bot Token**
   * Conserver ce token précieusement (ne jamais publier)

---

### 2️⃣ Configurer Supabase (Base de données SQL gratuite)

1. Se connecter à [Supabase](https://supabase.com/)
2. Créer un **nouveau projet**
3. Créer les **tables** via les scripts SQL : [Scripts SQL](SQL_des_tables_supabase.md)
4. Récupérer et noter :

   * **URL du projet** → `Project Settings → Data API → Project URL`
   * **Clé API** → `Project Settings → API Keys → Publishable Key` ou `Secret Key`

     * (La Publishable Key est recommandée, mais configurez les règles RLS sur vos tables pour sécuriser l’accès)

---

### 3️⃣ Préparer le fichier `.env` pour le bot

Créez un fichier `.env` à la racine du projet avec ces variables :

```env
DISCORD_TOKEN=VOTRE_BOT_TOKEN_ICI
COMMAND_PREFIX=!
SUPABASE_URL=VOTRE_SUPABASE_URL_ICI
SUPABASE_KEY=VOTRE_SUPABASE_KEY_ICI
PING_URL=VOTRE_URL_RENDER_ICI  # Exemple : https://monbot.onrender.com
```

* `DISCORD_TOKEN` → Token du bot Discord
* `COMMAND_PREFIX` → Préfixe utilisé pour les commandes (ex: `!`)
* `SUPABASE_URL` → URL de votre projet Supabase
* `SUPABASE_KEY` → Clé API Supabase
* `PING_URL` → URL de votre service Render (utilisée pour le self-ping afin que Render ne mette pas le bot en veille)

---

### 4️⃣ Déployer le bot sur Render

1. Se connecter à [Render](https://render.com/)
2. Cliquer sur **New → Web Service**
3. Sélectionner le **dépôt GitHub** contenant le bot
4. Choisir le **plan gratuit** pour l’instance
5. Dans **Startup Command**, mettre :

```bash
python bot.py
```

6. Dans **Environment Variables**, ajouter exactement celles que vous avez définies dans `.env`

---

### 5️⃣ Self-Ping avec `keep_alive.py`

Le bot est maintenant capable de **se maintenir en ligne tout seul**, grâce à `keep_alive.py` :

* Lance un petit serveur Flask qui répond aux pings HTTP
* Effectue un **ping automatique toutes les 5 minutes** sur l’URL de votre service Render (`PING_URL`)
* **Avantage** : vous n’êtes plus obligé d’utiliser UptimeRobot, Render gardera le bot actif automatiquement

Si vous voulez quand même utiliser UptimeRobot :

* Configurez un monitor HTTP(s) sur l’URL Render
* Intervalle recommandé : 5 minutes

---

## ⚠️ Notes importantes

* Cette méthode gratuite supporte **un nombre limité d’utilisateurs** (~100 max)
* Ne **jamais** publier votre Bot Token
* Le plan gratuit Render met le bot en veille si aucun ping n’est reçu → le self-ping `keep_alive.py` remplace entièrement UptimeRobot si configuré correctement

