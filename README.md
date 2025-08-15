
````markdown
# 🤖 Discord Bot – Render + Supabase + UptimeRobot

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-2.x-blueviolet.svg)
![Supabase](https://img.shields.io/badge/Supabase-SQL-green.svg)
![Render](https://img.shields.io/badge/Render-Free%20Hosting-orange.svg)
![Status](https://img.shields.io/badge/Status-Online-brightgreen.svg)

Un bot Discord utilisant **Supabase** pour la base de données, hébergé sur **Render**, et maintenu actif grâce à **UptimeRobot**.

---

## 📑 Table des matières
- [🚀 Technologies utilisées](#-technologies-utilisées)
- [📦 Installation & Configuration](#-installation--configuration)
  - [1️⃣ Créer et configurer l’application Discord](#1️⃣-créer-et-configurer-lapplication-discord)
  - [2️⃣ Configurer Supabase](#2️⃣-configurer-supabase-base-de-données-sql-gratuite)
  - [3️⃣ Déployer le bot sur Render](#3️⃣-déployer-le-bot-sur-render)
  - [4️⃣ Maintenir le bot en ligne avec UptimeRobot](#4️⃣-maintenir-le-bot-en-ligne-avec-uptimerobot)
- [📂 Structure du projet](#-structure-du-projet)
- [⚠️ Notes importantes](#️-notes-importantes)

---

## 🚀 Technologies utilisées
- **[Supabase](https://supabase.com/)** : Base de données SQL gratuite  
- **[Render](https://render.com/)** : Hébergeur gratuit pour le bot  
- **[UptimeRobot](https://uptimerobot.com/)** : Ping régulier pour garder le bot en ligne  
- **Python** : Langage principal du bot  

---

## 📦 Installation & Configuration

### 1️⃣ Créer et configurer l’application Discord
1. Se connecter au [Portail Développeur Discord](https://discord.com/developers/applications)  
2. **Créer une nouvelle application**  
3. Dans **General Information** :  
   - Noter l’`APPLICATION ID`  
4. Dans **Bot** :  
   - **Reset Token** pour obtenir le **Bot Token**  
   - Garder ce **Bot Token** privé  

---

### 2️⃣ Configurer Supabase (Base de données SQL gratuite)
1. Se connecter à [Supabase](https://supabase.com/)  
2. Créer un **nouveau projet**  
3. Créer les **tables** via les scripts SQL (à ajouter plus tard)  
4. Récupérer :  
   - **URL du projet**  
   - **Clé API**  
   *(à mettre dans `.env`)*  

---

### 3️⃣ Déployer le bot sur Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

1. Se connecter à [Render](https://render.com/)  
2. **New → Web Service**  
3. Sélectionner le **repo GitHub**  
4. Plan gratuit  
5. **Startup Command** :
   ```bash
   python bot.py
````

6. Dans **Settings → Environment Variables** :

   * `APP_ID` → Application ID Discord
   * `BOT_TOKEN` → Bot Token Discord
   * `SUPABASE_URL` → URL du projet Supabase
   * `SUPABASE_KEY` → Clé API Supabase
7. **Désactiver** Auto Deploy (plan gratuit limité)

---

### 4️⃣ Maintenir le bot en ligne avec UptimeRobot

1. Se connecter à [UptimeRobot](https://uptimerobot.com/)
2. **Nouveau monitor** :

   * Type : **HTTP(s)**
   * URL : Lien Render (onglet Events)
   * Intervalle : par défaut (5 min ou plus)

---

## 📂 Structure du projet

```
📦 MonBotDiscord
 ┣ 📜 bot.py
 ┣ 📜 requirements.txt
 ┣ 📜 .env.example
 ┗ 📂 cogs/          # Extensions du bot
```

---

## ⚠️ Notes importantes

* ❌ Ne publiez jamais votre **Bot Token** ou vos **clés API**
* 🔄 Redéployez manuellement après chaque modification de code
* ⏳ Le plan gratuit Render coupe le bot s’il n’est pas pingé

---

```
```
