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
[Scripts SQL](SQL_des_tables_supabase.md)
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
 votre bot en veille si aucun ping n’est reçu (d’où l’utilisation d’Up
timeRobot)

---
