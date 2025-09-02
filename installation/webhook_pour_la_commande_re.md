# 🔃 Redémarrer le bot Render via webhook

---

## 1️⃣ Créer le webhook Render

1. Connecte-toi à [Render](https://render.com/).
2. Ouvre ton service (ton bot).
3. Va dans **Settings → Build & Deploy → Deploy Hooks**.
4. Copie l’URL du deploy hook.
   👉 Exemple :

   ```
   https://api.render.com/deploy/srv-xxxxxx?key=yyyyyyyy
   ```

---

## 2️⃣ Ajouter la variable d’environnement

Dans Render → **Environment → Environment Variables**, ajoute :

```env
RENDER_REDEPLOY_WEBHOOK=https://api.render.com/deploy/srv-xxxxxx?key=yyyyyyyy
```

⚠️ Remplace `srv-xxxxxx` et `yyyyyyyy` par tes vraies valeurs.

Ensuite clique **Save Changes** et redeploy une fois ton bot pour que la variable soit prise en compte.

---

## 3️⃣ Utiliser dans ton code

Dans ta commande `!re` / `/re`, récupère la variable :

```python
self.render_webhook = os.getenv("RENDER_REDEPLOY_WEBHOOK")
```

Puis lance le redeploy via un `POST` sur ce webhook (la commande simplifiée le fait déjà).

---

## ✅ Résultat

Quand tu tapes `!re` ou `/re` :

1. Le bot annonce qu’il redémarre.
2. Il envoie la requête au webhook Render pour déclencher le redeploy.
3. Il prévient que le bot va bientôt être de retour 🔔
