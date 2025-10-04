# 📦 Installation & Configuration avec Render, Supabase et Uptime Robot

---

## 🚀 Outils utilisés

* **[Supabase](https://supabase.com/)** : Base de données SQL gratuite
* **[Render](https://render.com/)** : Hébergeur gratuit pour le bot
* **[UptimeRobot](https://uptimerobot.com/)** : Service pour pinger régulièrement le bot et le maintenir actif

---

### 1️⃣ Créer et configurer l’application Discord

1. Se connecter au [Portail Développeur Discord](https://discord.com/developers/applications)
2. **Créer une nouvelle application**
3. Dans **General Information** :

   * Noter l’`APPLICATION ID`, à conserver pour plus tard
4. Aller dans l’onglet **Bot** :

   * Cliquer sur **Reset Token** pour obtenir le **Bot Token**
   * Conserver ce **Bot Token** précieusement pour plus tard, ne jamais l'écrire quelque part de public

---

### 2️⃣ Configurer Supabase (Base de données SQL gratuite)

1. Se connecter à [Supabase](https://supabase.com/) (connexion GitHub possible)
2. Créer un **nouveau projet**
3. Créer les **tables** via les scripts SQL :
[Tables supabase](assets/SQL_des_tables_supabase)
4. Récupérer et mettre de côté :

   * **Le lien du projet (URL)** dans **Project Settings → Data API → Project URL**
   * **La clé API**  dans **Project Settings → API Keys → Publishable Keys ou Secret Keys** (Publishable c'est mieux mais après faut mettre des rls sur chaque table pour autoriser l'accès aux tables avec la clé)
---

### 3️⃣ Déployer le bot sur Render

1. Se connecter à [Render](https://render.com/) (compte Google ou création manuelle)
2. Cliquer sur **New → Web Service**
3. Sélectionner le **dépôt GitHub** contenant le bot
4. Choisir le **plan gratuit** dans le type d'instance
5. Dans **Startup Command**, mettre :

   ```bash
   python bot.py
   ```
6. Dans **Environment Variables**, ajouter les variables :

   * `APP_ID` → Application ID Discord
   * `BOT_TOKEN` → Bot Token Discord
   * `SUPABASE_URL` → URL du projet Supabase
   * `SUPABASE_KEY` → Clé API Supabase
   *  `COMMAND_PREFIX` → Préfixe pour les commandes 
7. Dans Advanced, chercher l’option auto-déploiement (**Auto Deploy**) et le mettre sur Off pour éviter de dépasser les limites du plan gratuit

---

### 4️⃣ Maintenir le bot en ligne avec UptimeRobot

1. Aller sur [UptimeRobot](https://uptimerobot.com/)
2. Créer un **nouveau monitor** :

   * Type : **HTTP(s)**
   * URL : Utiliser le lien généré par Render dans **Settings → Render Subdomain** 
   * Intervalle : par défaut (5 minutes ou plus)
3. Enregistrer pour que UptimeRobot ping régulièrement votre bot

---

## ⚠️ Notes importantes

* Cette façon d'héberger et déployer le bot gratuitement peut supporter que peu d'utilisateurs, pas plus d'une centaine je pense
* Ne **jamais** publier votre Bot Token quelque part de public
* Si vous modifiez le code, pensez à redéployer manuellement sur Render
* Le plan gratuit Render met votre bot en veille si aucun ping n’est reçu (d’où l’utilisation d’UptimeRobot)

---


