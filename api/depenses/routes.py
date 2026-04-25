"""
Routes pour la gestion des dépenses
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from crud import depense as crud_depense
from crud import activite as crud_activite
from database.schemas import DepenseCreate, DepenseRead
from api.dependencies import get_db
from security import require_module_access

router = APIRouter(
    prefix="/api/depenses",
    tags=["depenses"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


@router.get("", response_model=List[DepenseRead])
def get_depenses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer toutes les dépenses"""
    return crud_depense.get_depenses(db, skip=skip, limit=limit)


@router.get("/{depense_id}", response_model=DepenseRead)
def get_depense(depense_id: int, db: Session = Depends(get_db)):
    """Récupérer une dépense par ID"""
    db_depense = crud_depense.get_depense(db, depense_id)
    if not db_depense:
        raise HTTPException(status_code=404, detail="Dépense non trouvée")
    return db_depense


@router.get("/activites/{activite_id}", response_model=List[DepenseRead])
def get_depenses_by_activite(activite_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer les dépenses d'une activité"""
    activite = crud_activite.get_activite(db, activite_id)
    if not activite:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    
    return crud_depense.get_depenses_by_activite(db, activite_id, skip=skip, limit=limit)


@router.post("", response_model=DepenseRead, status_code=status.HTTP_201_CREATED)
def create_depense(payload: DepenseCreate, db: Session = Depends(get_db)):
    """Créer une nouvelle dépense"""
    # Vérifier que l'activité existe
    activite = crud_activite.get_activite(db, payload.id_activite)
    if not activite:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    
    return crud_depense.create_depense(db, payload)


@router.put("/{depense_id}", response_model=DepenseRead)
def update_depense(depense_id: int, payload: dict, db: Session = Depends(get_db)):
    """Mettre à jour une dépense"""
    db_depense = crud_depense.get_depense(db, depense_id)
    if not db_depense:
        raise HTTPException(status_code=404, detail="Dépense non trouvée")
    
    return crud_depense.update_depense(db, db_depense, payload)


@router.delete("/{depense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_depense(depense_id: int, db: Session = Depends(get_db)):
    """Supprimer une dépense"""
    db_depense = crud_depense.get_depense(db, depense_id)
    if not db_depense:
        raise HTTPException(status_code=404, detail="Dépense non trouvée")
    
    crud_depense.delete_depense(db, db_depense)
