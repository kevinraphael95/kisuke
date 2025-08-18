![kisuke](assets/kisuke.jpg)

# Kisuke Urahara - Bot Discord

👍 **Description :** Kisuke Urahara est un bot Discord très très amateur, en python, inspiré de Bleach. Il propose peu de commandes amusantes et un mini-jeu de collecte de "reiatsu" (qui ne sert à rien à part en avoir plus que les autres).

---

## 🛠️ Commandes du Bot


### 👑 Admin

* `heartbeat_admin` : x
* `reiatsu_admin` : x
* `re` : x
* `rpgreset` : x


### ⚔️ Bleach

* `bmoji` : Devine quel personnage Bleach se cache derrière ces emojis.
* `combat` : Lance un combat automatisé sur 5 tours entre 2 personnages tirés au hasard.
* `division` : Détermine ta division dans le Gotei 13.
* `kido` : Lance un sort de Kidō !
* `kluboutside` : Affiche une question de la FAQ du Klub Outside.
* `ship` : Calcule la compatibilité entre deux personnes.
* `tupref` : Choisis ton personnage préféré entre deux propositions aléatoires.

### 🎉 Fun

* `couleur` : Affiche une couleur aléatoire avec un aperçu visuel et ses codes HEX & RGB.
* `gay` : Calcule ton taux de gaytitude.
* `mastermind` : Joue au Mastermind.
* `pendu` : Joue au Pendu.
* `pizza` : Pizza aléatoire.

### 📚 Général

* `code` : Lien vers le code github
* `emoji` : Affiche tous les emojis animés du serveur ou un ou plusieurs.
* `help` : Affiche l’aide et la liste des commandes.
* `react` : Fait réagir le bot avec un emoji.
* `say` : Répète un message

### 🔮 Reiatsu

* `classe` : Choisir sa classe pour le minijeu des reiatsu.
* `reiatsu` : Commande principale pour le minijeu de récolte des reiatsu.
* `reiatsuvol` : Permet de voler du Reiatsu à quelqu’un.
* `steamkey` : Lotterie, 1% de chance de gagner une clé steam en échanges de reiatsu.
* `skill` : fonctionne pas


### ⚙️ Tâches & comportements automatiques

* `tasks/heartbeat.py` : Si activé, le bote envoie un message toute les 5 minutes dans le salon souhaité, permet de garder le bot en ligne dans l'évetualité où render désactive momentanément le serveur pour le keep-alive.
* `tasks/reiatsu_spawner.py` : Fait apparaître périodiquement des Reiatsu aléatoires dans un canal.

---

# 📦 Installation & Configuration avec supabase et render

## 🚀 Outils utilisés

* **[Supabase](https://supabase.com/)** : Base de données SQL gratuite.
* **[Render](https://render.com/)** : Hébergeur gratuit pour le bot.
* **[UptimeRobot](https://uptimerobot.com/)** : Service pour maintenir le bot actif.

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

create table public.reiatsu (
  user_id text not null,
  username text not null,
  points bigint not null,
  last_steal_attempt timestamp without time zone null,
  steal_cd smallint null,
  classe text null default 'Travailleur'::text,
  comp_cd timestamp with time zone null,
  bonus5 smallint null default '0'::smallint,
  created_at timestamp with time zone not null default now(),
  constraint reiatsu2_pkey primary key (user_id)
) TABLESPACE pg_default;

4.  Récupérer :

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

## 📝 À faire / fonctionnalités prévues

* **Préfixe custom par serveur** : permettre aux serveurs de remplacer le préfixe par défaut.
* **Cooldown personnalisable pour le spawn de Reiatsu** : ajuster la fréquence entre deux spawns par serveur.

---
