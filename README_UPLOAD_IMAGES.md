# Upload d'images (Guide debutant)

Ce document explique, pas a pas, la fonctionnalite d'upload d'image ajoutee pour:
- `utilisateur.image_utilisateur`
- `site.image_site`

Objectif:
- choisir une image dans un formulaire
- l'uploader vers FastAPI
- enregistrer l'URL retournee en base de donnees
- reafficher l'image dans les tableaux et les details

---

## 1) Comment fonctionne le flux complet

1. L'utilisateur choisit un fichier image dans le formulaire (`<input type="file">`).
2. Le frontend envoie ce fichier en `multipart/form-data` vers `POST /api/uploads/image`.
3. FastAPI:
   - valide le type de fichier (`image/*`)
   - valide l'extension (`.jpg/.jpeg/.png/.webp/.gif`)
   - valide la taille max (5MB)
   - sauvegarde le fichier dans le dossier `backend/uploads`
   - renvoie une URL comme `/uploads/abc123.png`
4. Le frontend prend cette URL et la place dans le payload JSON (`image_utilisateur` ou `image_site`).
5. Le `create/update` de l'entite enregistre cette URL en BDD.
6. Pour afficher l'image, le frontend reconstruit l'URL complete:
   - ex: `http://127.0.0.1:8000/uploads/abc123.png`

---

## 2) Ce qui a ete ajoute (backend)

### Route d'upload image
- Fichier: `api/uploads/routes.py`
- Endpoint: `POST /api/uploads/image`
- Reponse exemple:

```json
{
  "filename": "f3a8....png",
  "url": "/uploads/f3a8....png",
  "size": 124532,
  "content_type": "image/png"
}
```

### Exposition des fichiers statiques
- Fichier: `main.py`
- Ajout:
  - creation du dossier `uploads` si absent
  - `app.mount("/uploads", StaticFiles(...))`

Cela permet d'acceder au fichier via URL HTTP:
- `GET /uploads/<nom_fichier>`

### Enregistrement de la route
- Fichier: `api/__init__.py`
- Le router `uploads` est inclus dans l'app.

### Schemas utilisateur
- Fichier: `database/schemas.py`
- Ajout de `image_utilisateur` dans:
  - `UtilisateurCreate`
  - `UtilisateurUpdate`

### Reponse auth utilisateur
- Fichier: `api/utilisateurs/routes.py`
- Ajout de `image_utilisateur` dans:
  - la reponse du login
  - la route `/api/utilisateurs/auth/me`

---

## 3) Ce qui a ete ajoute (frontend)

### Service API upload
- Fichier: `frontend/Teambuildingmanagementapp/src/service/api.js`
- Methode:
  - `uploadAPI.uploadImage(file)`

Elle envoie un `FormData`:
- champ `file` = fichier image

### Formulaires modifies
- `src/app/pages/Utilisateurs.vue`
- `src/app/pages/Sites.vue`

Ajouts:
- `input file`
- preview locale (via URL retournee)
- upload avant `create/update`
- stockage de l'URL dans `image_utilisateur` / `image_site`
- affichage image dans modale details (et colonne image pour sites)

---

## 4) Pourquoi on uploade d'abord, puis on cree/modifie

On fait 2 appels:

1. Upload fichier:
- `POST /api/uploads/image`
- resultat: URL image

2. Sauvegarde de l'entite:
- `POST /api/utilisateurs` ou `PUT /api/utilisateurs/{id}`
- `POST /api/sites` ou `PUT /api/sites/{id}`
- avec `image_utilisateur` ou `image_site` = URL retournee

Avantage:
- le backend metier reste simple (JSON classique)
- l'upload est centralise dans un seul endpoint

---

## 5) Exemple simple de formulaire image (principe)

```vue
<input type="file" accept="image/*" @change="onImageChange" />
```

```js
const selectedFile = ref(null)

const onImageChange = (e) => {
  selectedFile.value = e?.target?.files?.[0] || null
}

const uploadImageIfNeeded = async () => {
  if (!selectedFile.value) return null
  const uploaded = await uploadAPI.uploadImage(selectedFile.value)
  return uploaded.url
}

const submit = async () => {
  const imageUrl = await uploadImageIfNeeded()
  await api.create({
    nom: form.nom,
    image_site: imageUrl
  })
}
```

---

## 6) Important: migration BDD

Si ta base existe deja, modifier `models.py` ne suffit pas.
Il faut ajouter les colonnes en base.

Exemple SQL (PostgreSQL):

```sql
ALTER TABLE utilisateur ADD COLUMN IF NOT EXISTS image_utilisateur VARCHAR(500);
ALTER TABLE site ADD COLUMN IF NOT EXISTS image_site VARCHAR(500);
```

Sans cela, tu peux avoir des erreurs SQL au `create/update`.

---

## 7) Comment tester rapidement

1. Lancer backend FastAPI
2. Lancer frontend
3. Ouvrir page `Utilisateurs` ou `Sites`
4. Ouvrir modale create/update
5. Choisir une image
6. Enregistrer
7. Verifier:
   - le fichier est dans `backend/uploads`
   - l'URL est en base
   - l'image s'affiche dans l'interface

---

## 8) Erreurs frequentes

- `422 Unprocessable Entity` sur upload:
  - souvent le champ n'est pas `file` dans le `FormData`
- image ne s'affiche pas:
  - URL incomplete ou mauvaise base URL
  - route statique `/uploads` non montee
- erreur SQL colonne inconnue:
  - migration BDD non executee
- fichier refuse:
  - extension non autorisee ou > 5MB

---

## 9) Resume mental (a retenir)

- L'image n'est pas envoyee dans le JSON directement.
- On envoie le fichier en `multipart/form-data`.
- Le backend renvoie une URL.
- Cette URL est stockee dans la table.
- Pour afficher, on utilise cette URL.

