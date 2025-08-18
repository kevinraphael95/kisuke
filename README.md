![kisuke](assets/kisuke.jpg)

# Kisuke Urahara - Bot Discord

👍 Description : Bot Discord multi-serveurs avec commandes personnalisables et gestion de spawns de Reiatsu.

---

## 🛠️ Commandes du Bot

**Préfixe par défaut** : `os.getenv("COMMAND_PREFIX", "!")`
Modules chargés dynamiquement. Certaines tâches automatiques peuvent être actives : `tasks.heartbeat` (ping toutes les 60s), `tasks.reiatsu_spawner` (spawn aléatoire de Reiatsu).

---

### 👑 Admin

| Commande          | Description                                          |
| ----------------- | ---------------------------------------------------- |
| `heartbeat_admin` | Vérifie que le bot est actif, renvoie un pong / état |
| `spawn_reiatsu`   | Force l’apparition d’un Reiatsu (administratif)      |
| `re`              | Recharge une extension                               |
| `rpgreset`        | Réinitialise les données RPG                         |

---

### ⚔️ Bleach

| Commande | Description                                   |
| -------- | --------------------------------------------- |
| `bmoji`  | Affiche des emojis liés à Bleach              |
| `kido`   | Utilisation de techniques Kido                |
| `ship`   | Calcule la compatibilité entre deux personnes |
| `tupref` | Affiche le préfixe configuré du serveur       |

---

### 🎉 Fun

| Commande     | Description                  |
| ------------ | ---------------------------- |
| `gay`        | Commande fun aléatoire       |
| `mastermind` | Joue au jeu du Mastermind    |
| `pendu`      | Joue au jeu du Pendu         |
| `couleur`    | Jeu de devinette de couleurs |
| `emoji`      | Génère un emoji custom       |
| `say`        | Fait parler le bot           |
| `pizza`      | Semble inactif ou buggué     |

---

### 📚 General

| Commande | Description                              |
| -------- | ---------------------------------------- |
| `code`   | Génère du code                           |
| `react`  | Fait réagir le bot avec un emoji         |
| `help`   | Affiche l’aide et la liste des commandes |

---

### 🔮 Reiatsu

| Commande     | Description                               |
| ------------ | ----------------------------------------- |
| `reiatsu`    | Affiche ton énergie Reiatsu               |
| `reiatsuvol` | Permet de voler du Reiatsu à quelqu’un    |
| `steamkey`   | Donne une clé Steam (fun/lotterie)        |
| `skill`      | Semble inactif ou non chargé correctement |

---

### 🧪 Test

| Commande    | Description                 |
| ----------- | --------------------------- |
| `testtache` | Test des tâches périodiques |
| `hollow`    | Test lié aux Hollows        |
| `test`      | Fonction de test générique  |

---

### ⚙️ Tâches & comportements automatiques

| Tâche                      | Description                                                         |
| -------------------------- | ------------------------------------------------------------------- |
| `tasks/heartbeat.py`       | Ping le bot toutes les 60 secondes pour vérifier qu’il répond       |
| `tasks/reiatsu_spawner.py` | Fait apparaître périodiquement des Reiatsu aléatoires dans un canal |

---

# 📦 Installation & Configuration avec Render, Supabase et Uptime Robot

## 🚀 Outils utilisés

* **[Supabase](https://supabase.com/)** : Base de données SQL gratuite
* **[Render](https://render.com/)** : Hébergeur gratuit pour le bot
* **[UptimeRobot](https://uptimerobot.com/)** : Service pour maintenir le bot actif
* **Python** : Langage principal du bot

---

## 1️⃣ Créer et configurer l’application Discord

1. Se connecter au [Portail Développeur Discord](https://discord.com/developers/applications)
2. **Créer une nouvelle application**
3. Dans **General Information** :

   * Noter l’`APPLICATION ID` (à conserver)
4. Aller dans l’onglet **Bot** :

   * Cliquer sur **Reset Token** pour obtenir le **Bot Token**
   * Conserver ce **Bot Token** précieusement

---

## 2️⃣ Configurer Supabase (Base de données SQL gratuite)

1. Se connecter à [Supabase](https://supabase.com/)
2. Créer un **nouveau projet**
3. Créer les **tables** via les scripts SQL (à ajouter dans la doc)
4. Récupérer :

   * **Lien du projet (URL)**
   * **Clé API**
     *(Ces deux valeurs seront utilisées dans `.env`)*

---

## 3️⃣ Déployer le bot sur Render

1. Se connecter à [Render](https://render.com/)
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
   * `COMMAND_PREFIX` → Préfixe par défaut pour les commandes

7. **Désactiver Auto Deploy** pour éviter de dépasser les limites du plan gratuit

---

## 4️⃣ Maintenir le bot en ligne avec UptimeRobot

1. Aller sur [UptimeRobot](https://uptimerobot.com/)
2. Créer un **nouveau monitor** :

   * Type : **HTTP(s)**
   * URL : Lien généré par Render (**Settings → Render Subdomain**)
   * Intervalle : par défaut (5 minutes)
3. Enregistrer pour que UptimeRobot ping régulièrement votre bot

---

## ⚠️ Notes importantes

* Ne **jamais** publier votre Bot Token ou vos clés Supabase
* Si vous modifiez le code, pensez à redéployer manuellement sur Render
* Le plan gratuit Render met votre bot en veille si aucun ping n’est reçu

---

## 📝 À faire / fonctionnalités prévues

* **Préfixe custom par serveur**

  * Permettre aux serveurs de remplacer le préfixe par défaut
* **Cooldown personnalisable pour le spawn de Reiatsu**

  * Chaque serveur peut ajuster la fréquence entre deux spawns

---

