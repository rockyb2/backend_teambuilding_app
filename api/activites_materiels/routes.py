"""
Routes pour la gestion du materiel affecte aux activites.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import activite as crud_activite
from crud import activite_materiel as crud_activite_materiel
from crud import materiel as crud_materiel
from database.schemas import (
    ActiviteMaterielCreate,
    ActiviteMaterielRead,
    ActiviteMaterielUpdate,
    MaterielDisponibiliteRead,
)
from security import require_module_access

router = APIRouter(
    prefix="/api/activites_materiels",
    tags=["activites_materiels"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


def _validate_materiel_actif(db_materiel) -> None:
    if db_materiel.statut is False:
        raise HTTPException(
            status_code=400,
            detail=f"Materiel inactif: {db_materiel.nom} ne peut pas etre reserve",
        )


@router.get("", response_model=List[ActiviteMaterielRead])
def get_activites_materiels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer toutes les affectations materiel."""
    return crud_activite_materiel.get_activites_materiels(db, skip=skip, limit=limit)


@router.get("/activites/{activite_id}", response_model=List[ActiviteMaterielRead])
def get_materiels_by_activite(activite_id: int, db: Session = Depends(get_db)):
    """Recuperer le materiel d'une activite."""
    if not crud_activite.get_activite(db, activite_id):
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    return crud_activite_materiel.get_materiels_by_activite(db, activite_id)


@router.get("/materiels/{materiel_id}", response_model=List[ActiviteMaterielRead])
def get_activites_by_materiel(materiel_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer les activites qui utilisent un materiel."""
    if not crud_materiel.get_materiel(db, materiel_id):
        raise HTTPException(status_code=404, detail="Materiel non trouve")

    return crud_activite_materiel.get_activites_by_materiel(db, materiel_id, skip=skip, limit=limit)


@router.get("/disponibilites", response_model=List[MaterielDisponibiliteRead])
def get_disponibilites_materiels(
    date_debut: datetime,
    date_fin: datetime,
    exclude_activite_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Calculer le stock reellement disponible pendant une periode."""
    if date_fin <= date_debut:
        raise HTTPException(status_code=400, detail="La date de fin doit etre apres la date de debut")

    return crud_activite_materiel.get_disponibilites_materiels(
        db,
        date_debut,
        date_fin,
        exclude_activite_id=exclude_activite_id,
    )


@router.get("/{activite_materiel_id}", response_model=ActiviteMaterielRead)
def get_activite_materiel(activite_materiel_id: int, db: Session = Depends(get_db)):
    """Recuperer une affectation materiel."""
    db_activite_materiel = crud_activite_materiel.get_activite_materiel(db, activite_materiel_id)
    if not db_activite_materiel:
        raise HTTPException(status_code=404, detail="Affectation materiel non trouvee")
    return db_activite_materiel


@router.post("", response_model=ActiviteMaterielRead, status_code=status.HTTP_201_CREATED)
def create_activite_materiel(payload: ActiviteMaterielCreate, db: Session = Depends(get_db)):
    """Ajouter du materiel a une activite."""
    db_activite = crud_activite.get_activite(db, payload.activite_id)
    if not db_activite:
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    db_materiel = crud_materiel.get_materiel(db, payload.materiel_id)
    if not db_materiel:
        raise HTTPException(status_code=404, detail="Materiel non trouve")
    _validate_materiel_actif(db_materiel)

    existing = crud_activite_materiel.get_activite_materiel_by_pair(db, payload.activite_id, payload.materiel_id)
    if existing:
        raise HTTPException(status_code=409, detail="Ce materiel est deja ajoute a cette activite")

    if crud_activite_materiel.activite_reserve_materiel(db_activite.statut):
        crud_activite_materiel.lock_materiel_reservation(db, db_materiel.id)
        quantite_disponible = crud_activite_materiel.get_quantite_disponible(
            db,
            db_materiel,
            db_activite.date_debut,
            db_activite.date_fin,
            exclude_activite_id=db_activite.id,
        )
        if payload.quantite_prevue > quantite_disponible:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuffisant pour {db_materiel.nom}: {quantite_disponible} disponible(s) sur cette periode",
            )

    return crud_activite_materiel.create_activite_materiel(db, payload)


@router.put("/{activite_materiel_id}", response_model=ActiviteMaterielRead)
def update_activite_materiel(
    activite_materiel_id: int,
    payload: ActiviteMaterielUpdate,
    db: Session = Depends(get_db),
):
    """Mettre a jour une affectation materiel."""
    db_activite_materiel = crud_activite_materiel.get_activite_materiel(db, activite_materiel_id)
    if not db_activite_materiel:
        raise HTTPException(status_code=404, detail="Affectation materiel non trouvee")

    updates = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    if "quantite_prevue" in updates and updates["quantite_prevue"] is not None:
        db_materiel = crud_materiel.get_materiel(db, db_activite_materiel.materiel_id)
        db_activite = crud_activite.get_activite(db, db_activite_materiel.activite_id)
        _validate_materiel_actif(db_materiel)
        if crud_activite_materiel.activite_reserve_materiel(db_activite.statut):
            crud_activite_materiel.lock_materiel_reservation(db, db_materiel.id)
            quantite_disponible = crud_activite_materiel.get_quantite_disponible(
                db,
                db_materiel,
                db_activite.date_debut,
                db_activite.date_fin,
                exclude_activite_id=db_activite.id,
            )
            if updates["quantite_prevue"] > quantite_disponible:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuffisant pour {db_materiel.nom}: {quantite_disponible} disponible(s) sur cette periode",
                )

    return crud_activite_materiel.update_activite_materiel(db, db_activite_materiel, payload)


@router.delete("/{activite_materiel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activite_materiel(activite_materiel_id: int, db: Session = Depends(get_db)):
    """Retirer du materiel d'une activite."""
    db_activite_materiel = crud_activite_materiel.get_activite_materiel(db, activite_materiel_id)
    if not db_activite_materiel:
        raise HTTPException(status_code=404, detail="Affectation materiel non trouvee")

    crud_activite_materiel.delete_activite_materiel(db, db_activite_materiel)
