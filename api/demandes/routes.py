"""
Routes pour la gestion des demandes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from crud import demande as crud_demande
from crud import client as crud_client
from database.schemas import DemandeCreate, DemandeRead
from api.dependencies import get_db

router = APIRouter(prefix="/api/demandes", tags=["demandes"])


@router.get("", response_model=List[DemandeRead])
def get_demandes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer toutes les demandes"""
    return crud_demande.get_demandes(db, skip=skip, limit=limit)


@router.get("/{demande_id}", response_model=DemandeRead)
def get_demande(demande_id: int, db: Session = Depends(get_db)):
    """Récupérer une demande par ID"""
    db_demande = crud_demande.get_demande(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    return db_demande


@router.get("/clients/{client_id}/demandes", response_model=List[DemandeRead])
def get_demandes_by_client(client_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer les demandes d'un client"""
    # Vérifier que le client existe
    client = crud_client.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    return crud_demande.get_demandes_by_client(db, client_id, skip=skip, limit=limit)


@router.post("", response_model=DemandeRead, status_code=status.HTTP_201_CREATED)
def create_demande(payload: DemandeCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle demande"""
    # Vérifier que le client existe
    client = crud_client.get_client(db, payload.id_client)
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    return crud_demande.create_demande(db, payload)


@router.put("/{demande_id}", response_model=DemandeRead)
def update_demande(demande_id: int, payload: dict, db: Session = Depends(get_db)):
    """Mettre à jour une demande"""
    db_demande = crud_demande.get_demande(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    return crud_demande.update_demande(db, db_demande, payload)


@router.delete("/{demande_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_demande(demande_id: int, db: Session = Depends(get_db)):
    """Supprimer une demande"""
    db_demande = crud_demande.get_demande(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    crud_demande.delete_demande(db, db_demande)
