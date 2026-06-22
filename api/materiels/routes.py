"""
Routes pour la gestion du materiel.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import activite_materiel as crud_activite_materiel
from crud import materiel as crud_materiel
from database.schemas import MaterielCreate, MaterielRead, MaterielUpdate
from security import require_module_access

router = APIRouter(
    prefix="/api/materiels",
    tags=["materiels"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


def _validate_stock_total_supports_reservations(db: Session, materiel_id: int, updates: dict) -> None:
    if "quantite_disponible" not in updates or updates["quantite_disponible"] is None:
        return

    nouvelle_quantite = int(updates["quantite_disponible"])
    crud_activite_materiel.lock_materiel_reservation(db, materiel_id)
    quantite_reservee_max = crud_activite_materiel.get_max_quantite_reservee(db, materiel_id)
    if nouvelle_quantite < quantite_reservee_max:
        raise HTTPException(
            status_code=400,
            detail=(
                "Impossible de baisser le stock total sous les reservations deja planifiees: "
                f"{quantite_reservee_max} unite(s) sont reservees sur au moins une periode"
            ),
        )


@router.get("", response_model=List[MaterielRead])
def get_materiels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer le materiel."""
    return crud_materiel.get_materiels(db, skip=skip, limit=limit)


@router.get("/{materiel_id}", response_model=MaterielRead)
def get_materiel(materiel_id: int, db: Session = Depends(get_db)):
    """Recuperer un materiel par ID."""
    db_materiel = crud_materiel.get_materiel(db, materiel_id)
    if not db_materiel:
        raise HTTPException(status_code=404, detail="Materiel non trouve")
    return db_materiel


@router.post("", response_model=MaterielRead, status_code=status.HTTP_201_CREATED)
def create_materiel(
    payload: MaterielCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Creer un materiel."""
    existing = crud_materiel.get_materiel_by_nom(db, payload.nom)
    if existing:
        raise HTTPException(status_code=409, detail="Materiel deja existant")

    payload.id_utilisateur_create = getattr(current_user, "id_utilisateur", None)
    return crud_materiel.create_materiel(db, payload)


@router.put("/{materiel_id}", response_model=MaterielRead)
def update_materiel(materiel_id: int, payload: MaterielUpdate, db: Session = Depends(get_db)):
    """Mettre a jour un materiel."""
    db_materiel = crud_materiel.get_materiel(db, materiel_id)
    if not db_materiel:
        raise HTTPException(status_code=404, detail="Materiel non trouve")

    updates = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    if "nom" in updates and updates["nom"] and updates["nom"] != db_materiel.nom:
        existing = crud_materiel.get_materiel_by_nom(db, updates["nom"])
        if existing:
            raise HTTPException(status_code=409, detail="Materiel deja existant")

    _validate_stock_total_supports_reservations(db, db_materiel.id, updates)
    return crud_materiel.update_materiel(db, db_materiel, payload)


@router.delete("/{materiel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_materiel(materiel_id: int, db: Session = Depends(get_db)):
    """Supprimer un materiel."""
    db_materiel = crud_materiel.get_materiel(db, materiel_id)
    if not db_materiel:
        raise HTTPException(status_code=404, detail="Materiel non trouve")

    crud_materiel.delete_materiel(db, db_materiel)
