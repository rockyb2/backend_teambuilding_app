from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import activite_materiel as crud_activite_materiel
from crud import materiel as crud_materiel
from database.models import Materiel
from database.schemas import (
    MaterielProductionCreate,
    MaterielProductionRead,
    MaterielProductionUpdate,
)
from security import require_module_access


router = APIRouter(
    prefix="/api/production/materiels",
    tags=["materiels production"],
    dependencies=[Depends(require_module_access("production"))],
)


def _payload_dump(payload, **kwargs):
    if hasattr(payload, "model_dump"):
        return payload.model_dump(**kwargs)
    return payload.dict(**kwargs)


def _inventory_name(marque: str, modele: str) -> str:
    return " ".join(part.strip() for part in (marque, modele) if part and part.strip())


def _production_values(payload: dict, db_materiel: Materiel | None = None) -> dict:
    marque = payload.get("marque", getattr(db_materiel, "marque", None))
    modele = payload.get("modele", getattr(db_materiel, "modele", None))
    if not marque or not str(marque).strip():
        raise HTTPException(status_code=422, detail="La marque est obligatoire")
    if not modele or not str(modele).strip():
        raise HTTPException(status_code=422, detail="Le modele est obligatoire")

    values = {
        "marque": str(marque).strip(),
        "modele": str(modele).strip(),
    }
    values["nom"] = _inventory_name(values["marque"], values["modele"])
    if "quantite" in payload and payload["quantite"] is not None:
        values["quantite_disponible"] = payload["quantite"]
    return values


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


def _get_production_materiel_or_404(db: Session, materiel_id: int) -> Materiel:
    db_materiel = crud_materiel.get_materiel(db, materiel_id)
    if not db_materiel or not db_materiel.marque or not db_materiel.modele:
        raise HTTPException(status_code=404, detail="Materiel de production non trouve")
    return db_materiel


@router.get("", response_model=List[MaterielProductionRead])
def get_materiels_production(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return (
        db.query(Materiel)
        .filter(Materiel.marque.isnot(None), Materiel.modele.isnot(None))
        .order_by(Materiel.marque.asc(), Materiel.modele.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{materiel_id}", response_model=MaterielProductionRead)
def get_materiel_production(materiel_id: int, db: Session = Depends(get_db)):
    return _get_production_materiel_or_404(db, materiel_id)


@router.post("", response_model=MaterielProductionRead, status_code=status.HTTP_201_CREATED)
def create_materiel_production(
    payload: MaterielProductionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("production")),
):
    values = _production_values(_payload_dump(payload))
    existing = crud_materiel.get_materiel_by_nom(db, values["nom"])
    if existing:
        raise HTTPException(status_code=409, detail="Materiel deja existant")

    values["description"] = None
    values["statut"] = True
    values["id_utilisateur_create"] = getattr(current_user, "id_utilisateur", None)
    return crud_materiel.create_materiel(db, values)


@router.put("/{materiel_id}", response_model=MaterielProductionRead)
def update_materiel_production(
    materiel_id: int,
    payload: MaterielProductionUpdate,
    db: Session = Depends(get_db),
):
    db_materiel = _get_production_materiel_or_404(db, materiel_id)
    updates = _production_values(_payload_dump(payload, exclude_unset=True), db_materiel)
    if updates["nom"] != db_materiel.nom:
        existing = crud_materiel.get_materiel_by_nom(db, updates["nom"])
        if existing and existing.id != db_materiel.id:
            raise HTTPException(status_code=409, detail="Materiel deja existant")

    _validate_stock_total_supports_reservations(db, db_materiel.id, updates)
    return crud_materiel.update_materiel(db, db_materiel, updates)


@router.delete("/{materiel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_materiel_production(materiel_id: int, db: Session = Depends(get_db)):
    db_materiel = _get_production_materiel_or_404(db, materiel_id)
    crud_materiel.delete_materiel(db, db_materiel)
