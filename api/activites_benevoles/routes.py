"""
Routes pour la gestion des benevoles affectes aux activites.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import activite as crud_activite
from crud import activite_benevole as crud_activite_benevole
from crud import benevole as crud_benevole
from database.schemas import ActiviteBenevoleCreate, ActiviteBenevoleRead, ActiviteBenevoleUpdate
from security import require_module_access

router = APIRouter(
    prefix="/api/activites_benevoles",
    tags=["activites_benevoles"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


@router.get("", response_model=List[ActiviteBenevoleRead])
def get_activites_benevoles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer toutes les affectations benevoles."""
    return crud_activite_benevole.get_activites_benevoles(db, skip=skip, limit=limit)


@router.get("/activites/{activite_id}", response_model=List[ActiviteBenevoleRead])
def get_benevoles_by_activite(activite_id: int, db: Session = Depends(get_db)):
    """Recuperer les benevoles d'une activite."""
    if not crud_activite.get_activite(db, activite_id):
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    return crud_activite_benevole.get_benevoles_by_activite(db, activite_id)


@router.get("/benevoles/{benevole_id}", response_model=List[ActiviteBenevoleRead])
def get_activites_by_benevole(benevole_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer les activites d'un benevole."""
    if not crud_benevole.get_benevole(db, benevole_id):
        raise HTTPException(status_code=404, detail="Benevole non trouve")

    return crud_activite_benevole.get_activites_by_benevole(db, benevole_id, skip=skip, limit=limit)


@router.get("/{activite_benevole_id}", response_model=ActiviteBenevoleRead)
def get_activite_benevole(activite_benevole_id: int, db: Session = Depends(get_db)):
    """Recuperer une affectation benevole."""
    db_activite_benevole = crud_activite_benevole.get_activite_benevole(db, activite_benevole_id)
    if not db_activite_benevole:
        raise HTTPException(status_code=404, detail="Affectation benevole non trouvee")
    return db_activite_benevole


@router.post("", response_model=ActiviteBenevoleRead, status_code=status.HTTP_201_CREATED)
def create_activite_benevole(payload: ActiviteBenevoleCreate, db: Session = Depends(get_db)):
    """Ajouter un benevole a une activite."""
    if not crud_activite.get_activite(db, payload.activite_id):
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    if not crud_benevole.get_benevole(db, payload.benevole_id):
        raise HTTPException(status_code=404, detail="Benevole non trouve")

    existing = crud_activite_benevole.get_activite_benevole_by_pair(db, payload.activite_id, payload.benevole_id)
    if existing:
        raise HTTPException(status_code=409, detail="Ce benevole est deja affecte a cette activite")

    return crud_activite_benevole.create_activite_benevole(db, payload)


@router.put("/{activite_benevole_id}", response_model=ActiviteBenevoleRead)
def update_activite_benevole(
    activite_benevole_id: int,
    payload: ActiviteBenevoleUpdate,
    db: Session = Depends(get_db),
):
    """Mettre a jour une affectation benevole."""
    db_activite_benevole = crud_activite_benevole.get_activite_benevole(db, activite_benevole_id)
    if not db_activite_benevole:
        raise HTTPException(status_code=404, detail="Affectation benevole non trouvee")

    return crud_activite_benevole.update_activite_benevole(db, db_activite_benevole, payload)


@router.delete("/{activite_benevole_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activite_benevole(activite_benevole_id: int, db: Session = Depends(get_db)):
    """Retirer un benevole d'une activite."""
    db_activite_benevole = crud_activite_benevole.get_activite_benevole(db, activite_benevole_id)
    if not db_activite_benevole:
        raise HTTPException(status_code=404, detail="Affectation benevole non trouvee")

    crud_activite_benevole.delete_activite_benevole(db, db_activite_benevole)
