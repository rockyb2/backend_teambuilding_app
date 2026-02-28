# Exemple de routes API FastAPI pour le backend
# À implémenter dans: backend/api/main.py ou backend/api/routes/

"""
Exemple d'implémentation FastAPI des routes API.
À adapter selon votre structure réelle du backend.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database.models import Client, Demande, Offre, Activite, Site, Jeu, Personnel, Affectation, Depense, Utilisateur, ActiviteJeu
from database.schemas import (
    ClientCreate, ClientRead,
    DemandeCreate, DemandeRead,
    OffreCreate, OffreRead,
    ActiviteCreate, ActiviteRead,
    SiteCreate, SiteRead,
    JeuCreate, JeuRead,
    PersonnelCreate, PersonnelRead,
    AffectationCreate, AffectationRead,
    DepenseCreate, DepenseRead,
    UtilisateurCreate, UtilisateurRead,
)
from database.connection import SessionLocal

app = FastAPI(title="Team Building Management API")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",      # Dev frontend Vite
        "http://localhost:3000",       # Alt dev
        "https://votredomaine.com",    # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dépendance pour obtenir la session DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============= CLIENTS =============
@app.get("/api/clients", response_model=List[ClientRead])
def get_clients(db: Session = Depends(get_db)):
    """Récupérer tous les clients"""
    return db.query(Client).all()

@app.get("/api/clients/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Récupérer un client par ID"""
    client = db.query(Client).filter(Client.id_client == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return client

@app.post("/api/clients", response_model=ClientRead, status_code=201)
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    """Créer un nouveau client"""
    # Vérifier l'email unique
    existing = db.query(Client).filter(Client.email == client.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    db_client = Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@app.put("/api/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, client: ClientCreate, db: Session = Depends(get_db)):
    """Modifier un client"""
    db_client = db.query(Client).filter(Client.id_client == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    for key, value in client.dict().items():
        setattr(db_client, key, value)
    
    db.commit()
    db.refresh(db_client)
    return db_client

@app.delete("/api/clients/{client_id}", status_code=204)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Supprimer un client"""
    db_client = db.query(Client).filter(Client.id_client == client_id).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    db.delete(db_client)
    db.commit()

# ============= DEMANDES =============
@app.get("/api/demandes", response_model=List[DemandeRead])
def get_demandes(db: Session = Depends(get_db)):
    """Récupérer toutes les demandes"""
    return db.query(Demande).all()

@app.get("/api/demandes/{demande_id}", response_model=DemandeRead)
def get_demande(demande_id: int, db: Session = Depends(get_db)):
    """Récupérer une demande"""
    demande = db.query(Demande).filter(Demande.id_demande == demande_id).first()
    if not demande:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    return demande

@app.get("/api/clients/{client_id}/demandes", response_model=List[DemandeRead])
def get_client_demandes(client_id: int, db: Session = Depends(get_db)):
    """Récupérer les demandes d'un client"""
    return db.query(Demande).filter(Demande.id_client == client_id).all()

@app.post("/api/demandes", response_model=DemandeRead, status_code=201)
def create_demande(demande: DemandeCreate, db: Session = Depends(get_db)):
    """Créer une demande"""
    # Vérifier que le client existe
    client = db.query(Client).filter(Client.id_client == demande.id_client).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    db_demande = Demande(**demande.dict())
    db.add(db_demande)
    db.commit()
    db.refresh(db_demande)
    return db_demande

@app.put("/api/demandes/{demande_id}", response_model=DemandeRead)
def update_demande(demande_id: int, demande: DemandeCreate, db: Session = Depends(get_db)):
    """Modifier une demande"""
    db_demande = db.query(Demande).filter(Demande.id_demande == demande_id).first()
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    for key, value in demande.dict().items():
        setattr(db_demande, key, value)
    
    db.commit()
    db.refresh(db_demande)
    return db_demande

@app.patch("/api/demandes/{demande_id}")
def patch_demande_status(demande_id: int, data: dict, db: Session = Depends(get_db)):
    """Changer le statut d'une demande (en_attente, en_etude, validee, refusee)"""
    db_demande = db.query(Demande).filter(Demande.id_demande == demande_id).first()
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    statuts_valides = {'en_attente', 'en_etude', 'validee', 'refusee'}
    nouveau_statut = data.get('statut')
    
    if nouveau_statut not in statuts_valides:
        raise HTTPException(status_code=400, detail=f"Statut invalide. Valides: {statuts_valides}")
    
    db_demande.statut = nouveau_statut
    db.commit()
    db.refresh(db_demande)
    return db_demande

@app.delete("/api/demandes/{demande_id}", status_code=204)
def delete_demande(demande_id: int, db: Session = Depends(get_db)):
    """Supprimer une demande"""
    db_demande = db.query(Demande).filter(Demande.id_demande == demande_id).first()
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    db.delete(db_demande)
    db.commit()

# ============= SITES =============
@app.get("/api/sites", response_model=List[SiteRead])
def get_sites(db: Session = Depends(get_db)):
    """Récupérer tous les sites"""
    return db.query(Site).all()

@app.get("/api/sites/{site_id}", response_model=SiteRead)
def get_site(site_id: int, db: Session = Depends(get_db)):
    """Récupérer un site"""
    site = db.query(Site).filter(Site.id_site == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return site

@app.post("/api/sites", response_model=SiteRead, status_code=201)
def create_site(site: SiteCreate, db: Session = Depends(get_db)):
    """Créer un site"""
    db_site = Site(**site.dict())
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site

@app.put("/api/sites/{site_id}", response_model=SiteRead)
def update_site(site_id: int, site: SiteCreate, db: Session = Depends(get_db)):
    """Modifier un site"""
    db_site = db.query(Site).filter(Site.id_site == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    for key, value in site.dict().items():
        setattr(db_site, key, value)
    
    db.commit()
    db.refresh(db_site)
    return db_site

@app.delete("/api/sites/{site_id}", status_code=204)
def delete_site(site_id: int, db: Session = Depends(get_db)):
    """Supprimer un site"""
    db_site = db.query(Site).filter(Site.id_site == site_id).first()
    if not db_site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    db.delete(db_site)
    db.commit()

# ============= AUTHENTIFICATION (exemple) =============
from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UtilisateurRead

@app.post("/api/auth/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Connexion utilisateur"""
    user = db.query(Utilisateur).filter(Utilisateur.email == credentials.email).first()
    
    if not user or not user.check_password(credentials.password):
        raise HTTPException(status_code=401, detail="Email ou mot de passe invalide")
    
    if not user.actif:
        raise HTTPException(status_code=403, detail="Compte désactivé")
    
    # Générer le token JWT (à implémenter selon vos besoins)
    # token = create_access_token({"sub": str(user.id_utilisateur)})
    
    return {
        "access_token": "fake-jwt-token-replace-with-real",  # À remplacer
        "token_type": "bearer",
        "user": UtilisateurRead.from_orm(user)
    }

@app.post("/api/auth/logout")
def logout():
    """Déconnexion (côté client: supprimer le token)"""
    return {"message": "Déconnecté"}

# ============= TEMPLATES POUR AUTRES RESSOURCES =============

# Les autres ressources suivent le même pattern:
# - GET /api/{resource}              (liste)
# - GET /api/{resource}/{id}         (détail)
# - POST /api/{resource}             (créer)
# - PUT /api/{resource}/{id}         (modifier)
# - PATCH /api/{resource}/{id}       (modifier partiellement)
# - DELETE /api/{resource}/{id}      (supprimer)

# À implémenter:
# - Offres (GET, POST, PUT, PATCH status, DELETE)
# - Activités (GET, POST, PUT, PATCH status, DELETE)
# - Jeux (GET, POST, PUT, DELETE)
# - Personnel (GET, POST, PUT, PATCH availability, DELETE)
# - Affectations (GET, POST, PUT, DELETE)
# - Dépenses (GET, POST, PUT, DELETE)
# - Utilisateurs (GET, POST, PUT, DELETE)
# - Activité-Jeu associations (POST, DELETE)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
