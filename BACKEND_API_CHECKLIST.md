# ✅ Backend API - Checklist d'implémentation

## 🏗️ Structure du backend

Le backend doit fournir les routes suivantes pour que le frontend fonctionne.

### 1️⃣ Routes Clients
```python
GET     /api/clients                 # Récupérer tous les clients
GET     /api/clients/{id}            # Récupérer un client
POST    /api/clients                 # Créer un client
PUT     /api/clients/{id}            # Modifier un client
DELETE  /api/clients/{id}            # Supprimer un client
```

#### Exemple de requête :
```bash
POST /api/clients
Content-Type: application/json

{
  "nom": "Dupont",
  "prenom": "Jean",
  "email": "jean@example.com",
  "entreprise": "Acme Corp",
  "telephone": "0123456789",
  "adresse": "123 Rue de la Paix"
}
```

#### Réponse attendue :
```json
{
  "id_client": 1,
  "nom": "Dupont",
  "prenom": "Jean",
  "email": "jean@example.com",
  "entreprise": "Acme Corp",
  "telephone": "0123456789",
  "adresse": "123 Rue de la Paix"
}
```

---

### 2️⃣ Routes Demandes
```python
GET     /api/demandes                        # Récupérer toutes les demandes
GET     /api/demandes/{id}                   # Récupérer une demande
GET     /api/clients/{client_id}/demandes   # Demandes d'un client
POST    /api/demandes                        # Créer une demande
PUT     /api/demandes/{id}                   # Modifier une demande
PATCH   /api/demandes/{id}                   # Changer le statut
DELETE  /api/demandes/{id}                   # Supprimer une demande
```

#### Statuts possibles :
- ✅ `en_attente` (défaut)
- ✅ `en_etude`
- ✅ `validee`
- ✅ `refusee`

#### Exemple PATCH (changement de statut) :
```bash
PATCH /api/demandes/1
Content-Type: application/json

{
  "statut": "en_etude"
}
```

---

### 3️⃣ Routes Offres
```python
GET     /api/offres                          # Récupérer toutes les offres
GET     /api/offres/{id}                     # Récupérer une offre
GET     /api/demandes/{demande_id}/offres   # Offres d'une demande
POST    /api/offres                          # Créer une offre
PUT     /api/offres/{id}                     # Modifier une offre
PATCH   /api/offres/{id}                     # Changer le statut
DELETE  /api/offres/{id}                     # Supprimer une offre
```

#### Statuts possibles :
- ✅ `brouillon` (défaut)
- ✅ `envoyee`
- ✅ `validee`
- ✅ `refusee`

---

### 4️⃣ Routes Activités
```python
GET     /api/activites                       # Récupérer toutes les activités
GET     /api/activites/{id}                  # Récupérer une activité
GET     /api/offres/{offre_id}/activites    # Activités d'une offre
GET     /api/sites/{site_id}/activites      # Activités d'un site
POST    /api/activites                       # Créer une activité
PUT     /api/activites/{id}                  # Modifier une activité
PATCH   /api/activites/{id}                  # Changer le statut
DELETE  /api/activites/{id}                  # Supprimer une activité
```

#### Statuts possibles :
- ✅ `planifiee` (défaut)
- ✅ `en_cours`
- ✅ `terminee`
- ✅ `annulee`

---

### 5️⃣ Routes Sites
```python
GET     /api/sites                   # Récupérer tous les sites
GET     /api/sites/{id}              # Récupérer un site
POST    /api/sites                   # Créer un site
PUT     /api/sites/{id}              # Modifier un site
DELETE  /api/sites/{id}              # Supprimer un site
```

---

### 6️⃣ Routes Jeux
```python
GET     /api/jeux                    # Récupérer tous les jeux
GET     /api/jeux/{id}               # Récupérer un jeu
POST    /api/jeux                    # Créer un jeu
PUT     /api/jeux/{id}               # Modifier un jeu
DELETE  /api/jeux/{id}               # Supprimer un jeu
```

---

### 7️⃣ Routes Activité-Jeu (Association)
```python
POST    /api/activites/{id}/jeux               # Ajouter un jeu
DELETE  /api/activites/{act_id}/jeux/{jeu_id} # Retirer un jeu
PUT     /api/activites/{act_id}/jeux/{jeu_id} # Modifier l'association
```

---

### 8️⃣ Routes Personnel
```python
GET     /api/personnel                # Récupérer tout le personnel
GET     /api/personnel/{id}           # Récupérer une personne
POST    /api/personnel                # Ajouter une personne
PUT     /api/personnel/{id}           # Modifier une personne
PATCH   /api/personnel/{id}           # Changer la disponibilité
DELETE  /api/personnel/{id}           # Supprimer une personne
```

---

### 9️⃣ Routes Affectations
```python
GET     /api/affectations                        # Toutes les affectations
GET     /api/affectations/{id}                   # Une affectation
GET     /api/activites/{act_id}/affectations    # Affectations d'une activité
GET     /api/personnel/{pers_id}/affectations   # Affectations d'une personne
POST    /api/affectations                        # Créer une affectation
PUT     /api/affectations/{id}                   # Modifier une affectation
DELETE  /api/affectations/{id}                   # Supprimer une affectation
```

---

### 🔟 Routes Dépenses
```python
GET     /api/depenses                          # Toutes les dépenses
GET     /api/depenses/{id}                     # Une dépense
GET     /api/activites/{act_id}/depenses      # Dépenses d'une activité
POST    /api/depenses                          # Créer une dépense
PUT     /api/depenses/{id}                     # Modifier une dépense
DELETE  /api/depenses/{id}                     # Supprimer une dépense
```

---

### 1️⃣1️⃣ Routes Utilisateurs
```python
GET     /api/utilisateurs            # Récupérer tous les utilisateurs
GET     /api/utilisateurs/{id}       # Récupérer un utilisateur
POST    /api/utilisateurs            # Créer un utilisateur
PUT     /api/utilisateurs/{id}       # Modifier un utilisateur
DELETE  /api/utilisateurs/{id}       # Supprimer un utilisateur
```

---

### 1️⃣2️⃣ Routes Authentification
```python
POST    /api/auth/login              # Connexion
POST    /api/auth/logout             # Déconnexion
POST    /api/auth/verify             # Vérifier le token
POST    /api/auth/change-password    # Changer le mot de passe
```

#### Exemple login :
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

#### Réponse attendue :
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id_utilisateur": 1,
    "email": "user@example.com",
    "nom": "Dupont",
    "role": "admin"
  }
}
```

---

## 🔐 Authentification

L'API doit supporter l'authentification JWT :

1. **En-tête Authorization** :
   ```
   Authorization: Bearer {token}
   ```

2. **Erreur 401** si le token est absent ou expiré

3. **Erreur 403** si l'utilisateur n'a pas les permissions

---

## 🛡️ CORS Configuration

Le backend doit configurer les CORS pour accepter :
```python
# FastAPI example
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 📊 Format des réponses

### Liste :
```json
[
  { "id": 1, "nom": "Item 1" },
  { "id": 2, "nom": "Item 2" }
]
```

### Détail :
```json
{
  "id": 1,
  "nom": "Item 1",
  "email": "item@example.com"
}
```

### Erreur :
```json
{
  "detail": "Elemento non trovato" ou "Unauthorized"
}
```

Avec le status HTTP approprié :
- `200` OK
- `201` Created
- `400` Bad Request
- `401` Unauthorized
- `403` Forbidden
- `404` Not Found
- `500` Server Error

---

## 🧪 Tester l'API

Utilisez curl ou Postman :

```bash
# Récupérer tous les clients
curl http://localhost:8000/api/clients

# Créer un client
curl -X POST http://localhost:8000/api/clients \
  -H "Content-Type: application/json" \
  -d '{"nom":"Dupont","email":"dupont@example.com"}'

# Avec authentification
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/clients
```

---

## ✅ Checklist

- [ ] Routes CRUD pour Client
- [ ] Routes CRUD pour Demande
- [ ] Routes CRUD pour Offre
- [ ] Routes CRUD pour Activité
- [ ] Routes CRUD pour Site
- [ ] Routes CRUD pour Jeu
- [ ] Routes pour Activité-Jeu
- [ ] Routes CRUD pour Personnel
- [ ] Routes CRUD pour Affectation
- [ ] Routes CRUD pour Dépense
- [ ] Routes CRUD pour Utilisateur
- [ ] Routes d'authentification (login, logout, verify)
- [ ] CORS configuré correctement
- [ ] JWT implémenté
- [ ] Gestion des erreurs (400, 401, 404, 500)
- [ ] Headers Content-Type: application/json
- [ ] Validation des données (Pydantic)

