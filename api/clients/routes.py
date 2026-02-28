"""
Routes pour la gestion des clients
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from crud import client as crud_client
from database.schemas import ClientCreate, ClientRead, ClientUpdate
from database.models import Client
from api.dependencies import get_db

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=List[ClientRead])
def get_clients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer tous les clients"""
    return crud_client.get_clients(db, skip=skip, limit=limit)


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)):
    """Récupérer un client par ID"""
    db_client = crud_client.get_client(db, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return db_client


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    """Créer un nouveau client"""
    # Vérifier l'unicité de l'email
    if payload.email:
        existing = crud_client.get_client_by_email(db, payload.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    return crud_client.create_client(db, payload)


@router.put("/{client_id}", response_model=ClientRead)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un client"""
    db_client = crud_client.get_client(db, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    # Vérifier que le nouvel email n'existe pas (sauf si c'est le même email)
    if payload.email and payload.email != db_client.email:
        existing = crud_client.get_client_by_email(db, payload.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    return crud_client.update_client(db, db_client, payload)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)):
    """Supprimer un client"""
    db_client = crud_client.get_client(db, client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    crud_client.delete_client(db, db_client)
