# 📚 Documentation des Routes API

## 🎯 Endpoints disponibles

### 1️⃣ Clients (`/api/clients`)

```python
GET     /api/clients                 # Récupérer tous les clients
GET     /api/clients/{client_id}     # Récupérer un client
POST    /api/clients                 # Créer un client
PUT     /api/clients/{client_id}     # Modifier un client
DELETE  /api/clients/{client_id}     # Supprimer un client
```

### 2️⃣ Demandes (`/api/demandes`)

```python
GET     /api/demandes                        # Récupérer toutes les demandes
GET     /api/demandes/{demande_id}           # Récupérer une demande
GET     /api/demandes/clients/{client_id}   # Demandes d'un client
POST    /api/demandes                        # Créer une demande
PUT     /api/demandes/{demande_id}           # Modifier une demande
DELETE  /api/demandes/{demande_id}           # Supprimer une demande
```

### 3️⃣ Offres (`/api/offres`)

```python
GET     /api/offres                          # Récupérer toutes les offres
GET     /api/offres/{offre_id}               # Récupérer une offre
GET     /api/offres/demandes/{demande_id}   # Offres d'une demande
POST    /api/offres                          # Créer une offre
PUT     /api/offres/{offre_id}               # Modifier une offre
DELETE  /api/offres/{offre_id}               # Supprimer une offre
```

### 4️⃣ Sites (`/api/sites`)

```python
GET     /api/sites                   # Récupérer tous les sites
GET     /api/sites/{site_id}         # Récupérer un site
POST    /api/sites                   # Créer un site
PUT     /api/sites/{site_id}         # Modifier un site
DELETE  /api/sites/{site_id}         # Supprimer un site
```

### 5️⃣ Activités (`/api/activites`)

```python
GET     /api/activites                       # Récupérer toutes les activités
GET     /api/activites/{activite_id}         # Récupérer une activité
GET     /api/activites/offres/{offre_id}    # Activité d'une offre
GET     /api/activites/sites/{site_id}      # Activités d'un site
POST    /api/activites                       # Créer une activité
PUT     /api/activites/{activite_id}         # Modifier une activité
DELETE  /api/activites/{activite_id}         # Supprimer une activité
```

### 6️⃣ Jeux (`/api/jeux`)

```python
GET     /api/jeux                    # Récupérer tous les jeux
GET     /api/jeux/{jeu_id}           # Récupérer un jeu
POST    /api/jeux                    # Créer un jeu
PUT     /api/jeux/{jeu_id}           # Modifier un jeu
DELETE  /api/jeux/{jeu_id}           # Supprimer un jeu
```

### 7️⃣ Associations Activité-Jeu (`/api/activites_jeux`)

```python
GET     /api/activites_jeux                              # Récupérer toutes les associations
GET     /api/activites_jeux/activites/{activite_id}     # Jeux d'une activité
GET     /api/activites_jeux/{activite_id}/{jeu_id}      # Récupérer une association
POST    /api/activites_jeux                              # Créer une association
PUT     /api/activites_jeux/{activite_id}/{jeu_id}      # Modifier une association
DELETE  /api/activites_jeux/{activite_id}/{jeu_id}      # Supprimer une association
```

### 8️⃣ Personnel (`/api/personnel`)

```python
GET     /api/personnel                   # Récupérer tout le personnel
GET     /api/personnel/disponibles       # Personnel disponible
GET     /api/personnel/{personnel_id}    # Récupérer un membre
POST    /api/personnel                   # Créer un membre
PUT     /api/personnel/{personnel_id}    # Modifier un membre
DELETE  /api/personnel/{personnel_id}    # Supprimer un membre
```

### 9️⃣ Affectations (`/api/affectations`)

```python
GET     /api/affectations                              # Récupérer toutes les affectations
GET     /api/affectations/{affectation_id}             # Récupérer une affectation
GET     /api/affectations/activites/{activite_id}      # Affectations d'une activité
GET     /api/affectations/personnel/{personnel_id}     # Affectations d'un membre
POST    /api/affectations                              # Créer une affectation
PUT     /api/affectations/{affectation_id}             # Modifier une affectation
DELETE  /api/affectations/{affectation_id}             # Supprimer une affectation
```

### 🔟 Dépenses (`/api/depenses`)

```python
GET     /api/depenses                              # Récupérer toutes les dépenses
GET     /api/depenses/{depense_id}                 # Récupérer une dépense
GET     /api/depenses/activites/{activite_id}     # Dépenses d'une activité
POST    /api/depenses                              # Créer une dépense
PUT     /api/depenses/{depense_id}                 # Modifier une dépense
DELETE  /api/depenses/{depense_id}                 # Supprimer une dépense
```

### 1️⃣1️⃣ Utilisateurs (`/api/utilisateurs`)

```python
GET     /api/utilisateurs                    # Récupérer tous les utilisateurs
GET     /api/utilisateurs/actifs             # Utilisateurs actifs
GET     /api/utilisateurs/role/{role}        # Utilisateurs par rôle
GET     /api/utilisateurs/{utilisateur_id}   # Récupérer un utilisateur
POST    /api/utilisateurs                    # Créer un utilisateur
PUT     /api/utilisateurs/{utilisateur_id}   # Modifier un utilisateur
DELETE  /api/utilisateurs/{utilisateur_id}   # Supprimer un utilisateur
POST    /api/utilisateurs/auth/login         # Authentifier un utilisateur
```

---

## 📋 Exemples de requêtes

### Créer un client

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

### Créer une demande

```bash
POST /api/demandes
Content-Type: application/json

{
  "id_client": 1,
  "date_demande": "2026-02-23",
  "description": "Demande de team building",
  "nombre_participants": 50,
  "budget_estime": 5000.00,
  "statut": "en_attente"
}
```

### Créer un utilisateur

```bash
POST /api/utilisateurs
Content-Type: application/json

{
  "nom": "Martin",
  "prenom": "Sophie",
  "email": "sophie@example.com",
  "mot_de_passe": "SecurePassword123",
  "role": "manager",
  "actif": true
}
```

### S'authentifier

```bash
POST /api/utilisateurs/auth/login?email=sophie@example.com&password=SecurePassword123
```

---

## 🔒 Validation et contraintes

- **Emails uniques** : Client, Personnel, Utilisateur
- **Clés étrangères** : Vérifiées avant création/modification
- **Contraintes métier** : Respectées selon les modèles
- **Statuts limités** : Utiliser les valeurs prédéfinies

---

## 📊 Codes de réponse

| Code | Sens |
|------|------|
| 200 | OK - Opération réussie |
| 201 | Created - Ressource créée |
| 204 | No Content - Suppression réussie |
| 400 | Bad Request - Données invalides |
| 404 | Not Found - Ressource non trouvée |
| 500 | Server Error - Erreur serveur |

---

## 🚀 Démarrer le serveur

```bash
python runserver.py
```

L'API sera disponible à : `http://localhost:8000`
Documentation interactive : `http://localhost:8000/docs`
