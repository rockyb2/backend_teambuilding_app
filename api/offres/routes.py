"""
Routes pour la gestion des offres
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from crud import offre as crud_offre
from crud import demande as crud_demande
from database.schemas import OffreCreate, OffreRead
from api.dependencies import get_db
from security import require_module_access

router = APIRouter(
    prefix="/api/offres",
    tags=["offres"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


@router.get("", response_model=List[OffreRead])
def get_offres(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer toutes les offres"""
    return crud_offre.get_offres(db, skip=skip, limit=limit)


@router.get("/{offre_id}", response_model=OffreRead)
def get_offre(offre_id: int, db: Session = Depends(get_db)):
    """Récupérer une offre par ID"""
    db_offre = crud_offre.get_offre(db, offre_id)
    if not db_offre:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    return db_offre


@router.get("/demandes/{demande_id}", response_model=List[OffreRead])
def get_offres_by_demande(demande_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer les offres d'une demande"""
    # Vérifier que la demande existe
    demande = crud_demande.get_demande(db, demande_id)
    if not demande:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    return crud_offre.get_offres_by_demande(db, demande_id, skip=skip, limit=limit)


@router.post("", response_model=OffreRead, status_code=status.HTTP_201_CREATED)
def create_offre(payload: OffreCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle offre"""
    # Vérifier que la demande existe
    demande = crud_demande.get_demande(db, payload.id_demande)
    if not demande:
        raise HTTPException(status_code=404, detail="Demande non trouvée")
    
    return crud_offre.create_offre(db, payload)


@router.put("/{offre_id}", response_model=OffreRead)
def update_offre(offre_id: int, payload: dict, db: Session = Depends(get_db)):
    """Mettre à jour une offre"""
    db_offre = crud_offre.get_offre(db, offre_id)
    if not db_offre:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    return crud_offre.update_offre(db, db_offre, payload)


@router.delete("/{offre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offre(offre_id: int, db: Session = Depends(get_db)):
    """Supprimer une offre"""
    db_offre = crud_offre.get_offre(db, offre_id)
    if not db_offre:
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    
    crud_offre.delete_offre(db, db_offre)
