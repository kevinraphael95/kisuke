# 🔃 Redémarrage du bot avec redeploy Render via webhook

---

## 1️⃣ Créer un webhook Render

1. Connecte-toi à ton compte [Render](https://render.com/).
2. Va dans ton service bot.
3. Clique sur **Settings**.
4. Note l’ID du service (ex : `srv-xxxxxx`).
5. Dans **Build & Deploy → Deploy Hooks**, récupère l’URL du deploy hook. Elle ressemble à :  
```

[https://api.render.com/deploy/srv-xxxxxx](https://api.render.com/deploy/srv-xxxxxx)

```

---

## 2️⃣ Ajouter les variables d’environnement

1. Dans Render, va dans **Environment → Environment Variables**.
2. Ajoute une variable pour le webhook :  
```

RENDER\_REDEPLOY\_WEBHOOK=[https://api.render.com/deploy/srv-xxxxxx](https://api.render.com/deploy/srv-xxxxxx)

```
3. Ajoute aussi une variable pour l’API du service (pour vérifier que le service est actif après le redeploy) :  
```

RENDER\_SERVICE\_API=[https://api.render.com/v1/services/srv-xxxxxx](https://api.render.com/v1/services/srv-xxxxxx)

````
4. Sauvegarde et redeploy ton bot une dernière fois pour que les variables soient prises en compte.

---

## 3️⃣ Utiliser le webhook dans la commande

Dans la commande `!re` du bot, ajoute :

```python
self.render_webhook = os.getenv("RENDER_REDEPLOY_WEBHOOK")
self.render_service_api = os.getenv("RENDER_SERVICE_API")
````

Lorsque `!re` est exécuté :

* ✅ Le bot prévient les membres que le redeploy est imminent.
* ✅ Envoie la requête au webhook Render.
* ✅ Attend que le service soit de nouveau en ligne et notifie (optionnel).

```

---
