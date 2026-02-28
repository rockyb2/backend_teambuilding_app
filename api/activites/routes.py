"""
Routes pour la gestion des activités
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from crud import activite as crud_activite
from crud import offre as crud_offre
from crud import site as crud_site
from database.schemas import ActiviteCreate, ActiviteRead
from api.dependencies import get_db

router = APIRouter(prefix="/api/activites", tags=["activites"])


@router.get("", response_model=List[ActiviteRead])
def get_activites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer toutes les activités"""
    return crud_activite.get_activites(db, skip=skip, limit=limit)


@router.get("/{activite_id}", response_model=ActiviteRead)
def get_activite(activite_id: int, db: Session = Depends(get_db)):
    """Récupérer une activité par ID"""
    db_activite = crud_activite.get_activite(db, activite_id)
    if not db_activite:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    return db_activite


@router.get("/offres/{offre_id}", response_model=ActiviteRead)
def get_activite_by_offre(offre_id: int, db: Session = Depends(get_db)):
    """Récupérer l'activité d'une offre"""
    offre = crud_offre.get_offre(db, offre_id)
    if not offre:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    db_activite = crud_activite.get_activites_by_offre(db, offre_id)
    if not db_activite:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    return db_activite


@router.get("/sites/{site_id}", response_model=List[ActiviteRead])
def get_activites_by_site(site_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer les activités d'un site"""
    site = crud_site.get_site(db, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    return crud_activite.get_activites_by_site(db, site_id, skip=skip, limit=limit)


@router.post("", response_model=ActiviteRead, status_code=status.HTTP_201_CREATED)
def create_activite(payload: ActiviteCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle activité"""
    # Vérifier que le site existe
    site = crud_site.get_site(db, payload.id_site)
    if not site:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    
    # Vérifier que l'offre existe si elle est spécifiée
    if payload.id_offre:
        offre = crud_offre.get_offre(db, payload.id_offre)
        if not offre:
            raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    return crud_activite.create_activite(db, payload)


@router.put("/{activite_id}", response_model=ActiviteRead)
def update_activite(activite_id: int, payload: dict, db: Session = Depends(get_db)):
    """Mettre à jour une activité"""
    db_activite = crud_activite.get_activite(db, activite_id)
    if not db_activite:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    
    return crud_activite.update_activite(db, db_activite, payload)


@router.delete("/{activite_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activite(activite_id: int, db: Session = Depends(get_db)):
    """Supprimer une activité"""
    db_activite = crud_activite.get_activite(db, activite_id)
    if not db_activite:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    
    crud_activite.delete_activite(db, db_activite)
