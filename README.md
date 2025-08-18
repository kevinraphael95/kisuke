![kisuke](assets/kisuke.jpg)

# Kisuke Urahara - Bot Discord

👍 **Description :** Kisuke Urahara est un bot Discord en python inspiré de Bleach. Il propose peu de commandes amusantes et un mini-jeu de collecte de "reiatsu" (qui ne sert à rien à part en avoir plus que les autres).

---

## 🛠️ Commandes du Bot

**Préfixe par défaut** : `os.getenv("COMMAND_PREFIX", "!")`
Modules chargés dynamiquement. Certaines tâches automatiques peuvent être actives :
`tasks.heartbeat` (ping toutes les 60s), `tasks.reiatsu_spawner` (spawn aléatoire de Reiatsu).

### 👑 Admin

* `heartbeat_admin` : Vérifie que le bot est actif.
* `spawn_reiatsu` : Force l’apparition d’un Reiatsu.
* `re` : Recharge une extension.
* `rpgreset` : Réinitialise les données RPG.

### ⚔️ Bleach

* `bmoji` : Affiche des emojis liés à Bleach.
* `kido` : Utilisation de techniques Kido.
* `ship` : Calcule la compatibilité entre deux personnes.
* `tupref` : Affiche le préfixe configuré du serveur.

### 🎉 Fun

* `gay` : Commande amusante aléatoire.
* `mastermind` : Joue au Mastermind.
* `pendu` : Joue au Pendu.
* `couleur` : Jeu de devinette de couleurs.
* `emoji` : Génère un emoji custom.
* `say` : Fait parler le bot.
* `pizza` : Semble inactif ou buggué.

### 📚 Général

* `code` : Génère du code.
* `react` : Fait réagir le bot avec un emoji.
* `help` : Affiche l’aide et la liste des commandes.

### 🔮 Reiatsu

* `reiatsu` : Affiche ton énergie Reiatsu.
* `reiatsuvol` : Permet de voler du Reiatsu à quelqu’un.
* `steamkey` : Donne une clé Steam (fun/lotterie).
* `skill` : Semble inactif ou non chargé correctement.

### 🧪 Test

* `testtache` : Test des tâches périodiques.
* `hollow` : Test lié aux Hollows.
* `test` : Fonction de test générique.

### ⚙️ Tâches & comportements automatiques

* `tasks/heartbeat.py` : Ping le bot toutes les 60 secondes pour vérifier qu’il répond.
* `tasks/reiatsu_spawner.py` : Fait apparaître périodiquement des Reiatsu aléatoires dans un canal.

---

# 📦 Installation & Configuration

## 🚀 Outils utilisés

* **[Supabase](https://supabase.com/)** : Base de données SQL gratuite.
* **[Render](https://render.com/)** : Hébergeur gratuit pour le bot.
* **[UptimeRobot](https://uptimerobot.com/)** : Service pour maintenir le bot actif.
* **Python** : Langage principal du bot.

---

## 1️⃣ Créer et configurer l’application Discord

1. Se connecter au [Portail Développeur Discord](https://discord.com/developers/applications).
2. Créer une **nouvelle application**.
3. Dans **General Information** : noter l’`APPLICATION ID`.
4. Dans l’onglet **Bot** : cliquer sur **Reset Token** pour obtenir le **Bot Token**. Conserver précieusement.

---

## 2️⃣ Configurer Supabase

1. Se connecter à [Supabase](https://supabase.com/).
2. Créer un **nouveau projet**.
3. Créer les **tables** via les scripts SQL.
4. Récupérer :

   * **URL du projet**
   * **Clé API**
     *(Ces valeurs seront utilisées dans `.env`)*

---

## 3️⃣ Déployer le bot sur Render

1. Se connecter à [Render](https://render.com/).
2. Cliquer sur **New → Web Service**.
3. Sélectionner le **dépôt GitHub** contenant le bot.
4. Choisir le **plan gratuit**.
5. Dans **Startup Command** :

```bash
python bot.py
```

6. Dans **Settings → Environment Variables**, ajouter :

   * `APP_ID` → Application ID Discord
   * `BOT_TOKEN` → Bot Token Discord
   * `SUPABASE_URL` → URL du projet Supabase
   * `SUPABASE_KEY` → Clé API Supabase
   * `COMMAND_PREFIX` → Préfixe par défaut pour les commandes
7. **Désactiver Auto Deploy** pour éviter de dépasser les limites du plan gratuit.

---

## 4️⃣ Maintenir le bot en ligne avec UptimeRobot

1. Aller sur [UptimeRobot](https://uptimerobot.com/).
2. Créer un **nouveau monitor** :

   * Type : **HTTP(s)**
   * URL : Lien généré par Render
   * Intervalle : par défaut (5 minutes)
3. Enregistrer pour que le bot soit ping régulièrement.

---

## ⚠️ Notes importantes

* Ne **jamais** publier votre Bot Token ou vos clés Supabase.
* Si vous modifiez le code, redéployer manuellement sur Render.
* Le plan gratuit Render met votre bot en veille si aucun ping n’est reçu.

---

## 📝 À faire / fonctionnalités prévues

* **Préfixe custom par serveur** : permettre aux serveurs de remplacer le préfixe par défaut.
* **Cooldown personnalisable pour le spawn de Reiatsu** : ajuster la fréquence entre deux spawns par serveur.

---
