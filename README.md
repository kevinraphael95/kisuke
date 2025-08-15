---

# Discord Bot – Hébergé sur Render avec Supabase

Un bot Discord utilisant **Supabase** pour la base de données et hébergé gratuitement sur **Render**, avec un ping automatique via **UptimeRobot** pour rester en ligne.

---

## 🚀 Outils utilisées

* **[Supabase](https://supabase.com/)** : Base de données SQL gratuite
* **[Render](https://render.com/)** : Hébergeur gratuit pour le bot
* **[UptimeRobot](https://uptimerobot.com/)** : Service pour pinger régulièrement le bot et le maintenir actif
* **Python** : Langage principal du bot

---

## 📦 Installation & Configuration

### 1️⃣ Créer et configurer l’application Discord

1. Se connecter au [Portail Développeur Discord](https://discord.com/developers/applications)
2. **Créer une nouvelle application**
3. Dans **General Information** :

   * Noter l’`APPLICATION ID` (à conserver pour plus tard)
4. Aller dans l’onglet **Bot** :

   * Cliquer sur **Reset Token** pour obtenir le **Bot Token**
   * Conserver ce **Bot Token** précieusement

---

### 2️⃣ Configurer Supabase (Base de données SQL gratuite)

1. Se connecter à [Supabase](https://supabase.com/) (connexion GitHub possible)
2. Créer un **nouveau projet**
3. Créer les **tables** via les scripts SQL (à ajouter plus tard dans la doc)
4. Récupérer :

   * **Lien du projet (URL)**
   * **Clé API**
     *(Ces deux valeurs seront utilisées dans `.env`)*

---

### 3️⃣ Déployer le bot sur Render

1. Se connecter à [Render](https://render.com/) (compte Google ou création manuelle)
2. Cliquer sur **New → Web Service**
3. Sélectionner le **dépôt GitHub** contenant le bot
4. Choisir le **plan gratuit**
5. Dans **Startup Command**, mettre :

   ```bash
   python bot.py
   ```
6. Dans **Settings → Environment Variables**, ajouter :

   * `APP_ID` → Application ID Discord
   * `BOT_TOKEN` → Bot Token Discord
   * `SUPABASE_URL` → URL du projet Supabase
   * `SUPABASE_KEY` → Clé API Supabase
7. **Désactiver** l’auto-déploiement (**Auto Deploy**) pour éviter de dépasser les limites du plan gratuit

---

### 4️⃣ Maintenir le bot en ligne avec UptimeRobot

1. Aller sur [UptimeRobot](https://uptimerobot.com/)
2. Créer un **nouveau monitor** :

   * Type : **HTTP(s)**
   * URL : Lien violet généré par Render dans **Events**
   * Intervalle : par défaut (5 minutes ou plus)
3. Enregistrer pour que UptimeRobot ping régulièrement votre bot

---

## 📂 Structure du projet

```
📦 MonBotDiscord
 ┣ 📜 bot.py
 ┣ 📜 requirements.txt
 ┣ 📜 .env.example
 ┣ 📂 commands/
 ┣ 📂 tasks/
 ┗ 📂 utils/          
```

---

## ⚠️ Notes importantes

* Ne **jamais** publier votre Bot Token ou vos clés Supabase
* Si vous modifiez le code, pensez à redéployer manuellement sur Render
* Le plan gratuit Render a un temps d’inactivité si le bot n’est pas pingé (d’où UptimeRobot)

---

