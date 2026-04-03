# Deploiement sur Render

## 1. Preparer le depot

- pousse ce dossier sur GitHub
- verifie que `.env` n'est pas committe

## 2. Creer le service Render

Option recommandee:
- dans Render, choisis **New +**
- clique **Blueprint**
- connecte le repo GitHub
- Render detectera automatiquement `render.yaml`

Cela creera:
- un service web `teambuilding-backend`
- une base PostgreSQL `teambuilding-db`

## 3. Configurer les variables

Dans Render, renseigne les variables suivantes si elles sont utilisees:
- `CORS_ORIGINS`
- `MISTRAL_API_KEY`
- `BREVO_API_KEY`
- `SENDER_EMAIL`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_BASE_URL`

Exemple `CORS_ORIGINS`:

```text
https://ton-frontend.onrender.com,http://localhost:5173
```

## 4. Commandes utilisees

- build: `pip install -r requirements.txt`
- start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

## 5. Important pour les fichiers uploades

Render n'offre pas un stockage disque persistant fiable pour les fichiers uploads sur un service web classique.

Consequence:
- les fichiers dans `uploads/` peuvent disparaitre apres redemarrage ou redeploiement

Pour la production, il faudra idealement stocker les images sur:
- Cloudinary
- AWS S3
- Cloudflare R2
- Supabase Storage

## 6. Verifications apres deploy

- ouvre `/health`
- ouvre `/docs`
- teste une route API
- verifie que la connexion PostgreSQL fonctionne
