"""
Routes pour la gestion des affectations du personnel.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import affectation as crud_affectation
from crud import activite as crud_activite
from crud import personnel as crud_personnel
from database.schemas import AffectationCreate, AffectationRead
from security import require_module_access

router = APIRouter(
    prefix="/api/affectations",
    tags=["affectations"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


@router.get("", response_model=List[AffectationRead])
def get_affectations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer toutes les affectations."""
    return crud_affectation.get_affectations(db, skip=skip, limit=limit)


@router.get("/activites/{activite_id}", response_model=List[AffectationRead])
def get_affectations_by_activite(activite_id: int, db: Session = Depends(get_db)):
    """Recuperer les affectations d'une activite."""
    if not crud_activite.get_activite(db, activite_id):
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    return crud_affectation.get_affectations_by_activite(db, activite_id)


@router.get("/personnel/{personnel_id}", response_model=List[AffectationRead])
def get_affectations_by_personnel(personnel_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer les affectations d'un membre du personnel."""
    if not crud_personnel.get_personnel(db, personnel_id):
        raise HTTPException(status_code=404, detail="Personnel non trouve")

    return crud_affectation.get_affectations_by_personnel(db, personnel_id, skip=skip, limit=limit)


@router.get("/{affectation_id}", response_model=AffectationRead)
def get_affectation(affectation_id: int, db: Session = Depends(get_db)):
    """Recuperer une affectation par ID."""
    db_affectation = crud_affectation.get_affectation(db, affectation_id)
    if not db_affectation:
        raise HTTPException(status_code=404, detail="Affectation non trouvee")
    return db_affectation


@router.post("", response_model=AffectationRead, status_code=status.HTTP_201_CREATED)
def create_affectation(payload: AffectationCreate, db: Session = Depends(get_db)):
    """Creer une nouvelle affectation."""
    if not crud_activite.get_activite(db, payload.activite_id):
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    if not crud_personnel.get_personnel(db, payload.personnel_id):
        raise HTTPException(status_code=404, detail="Personnel non trouve")

    existing = crud_affectation.get_affectation_by_pair(db, payload.activite_id, payload.personnel_id)
    if existing:
        raise HTTPException(status_code=409, detail="Ce membre du personnel est deja affecte a cette activite")

    return crud_affectation.create_affectation(db, payload)


@router.put("/{affectation_id}", response_model=AffectationRead)
def update_affectation(affectation_id: int, payload: dict, db: Session = Depends(get_db)):
    """Mettre a jour une affectation."""
    db_affectation = crud_affectation.get_affectation(db, affectation_id)
    if not db_affectation:
        raise HTTPException(status_code=404, detail="Affectation non trouvee")

    return crud_affectation.update_affectation(db, db_affectation, payload)


@router.delete("/{affectation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_affectation(affectation_id: int, db: Session = Depends(get_db)):
    """Supprimer une affectation."""
    db_affectation = crud_affectation.get_affectation(db, affectation_id)
    if not db_affectation:
        raise HTTPException(status_code=404, detail="Affectation non trouvee")

    crud_affectation.delete_affectation(db, db_affectation)
