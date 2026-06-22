"""
Routes pour la gestion des offres team building.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from api.dependencies import get_db
from crud import demande_team_building as crud_demande_team_building
from crud import offre as crud_offre
from database.schemas import OffreCreate, OffreRead, OffreUpdate
from security import require_module_access

router = APIRouter(
    prefix="/api/offres",
    tags=["offres"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


def _payload_dump(payload, **kwargs):
    if hasattr(payload, "model_dump"):
        return payload.model_dump(**kwargs)
    return payload.dict(**kwargs)


@router.get("", response_model=List[OffreRead])
def get_offres(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer toutes les offres."""
    return crud_offre.get_offres(db, skip=skip, limit=limit)


@router.get("/demandes/{demande_id}", response_model=List[OffreRead])
def get_offres_by_demande(
    demande_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Recuperer les offres d'une demande team building."""
    demande = crud_demande_team_building.get_demande_team_building(db, demande_id)
    if not demande:
        raise HTTPException(status_code=404, detail="Demande non trouvee")

    return crud_offre.get_offres_by_demande(db, demande_id, skip=skip, limit=limit)


@router.get("/{offre_id}", response_model=OffreRead)
def get_offre(offre_id: int, db: Session = Depends(get_db)):
    """Recuperer une offre par ID."""
    db_offre = crud_offre.get_offre(db, offre_id)
    if not db_offre:
        raise HTTPException(status_code=404, detail="Offre non trouvee")
    return db_offre


@router.post("", response_model=OffreRead, status_code=status.HTTP_201_CREATED)
def create_offre(
    payload: OffreCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Creer une nouvelle offre."""
    demande = crud_demande_team_building.get_demande_team_building(db, payload.demande_id)
    if not demande:
        raise HTTPException(status_code=404, detail="Demande non trouvee")

    return crud_offre.create_offre(
        db,
        payload,
        created_by_id=getattr(current_user, "id_utilisateur", None),
    )


@router.put("/{offre_id}", response_model=OffreRead)
def update_offre(
    offre_id: int,
    payload: OffreUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Mettre a jour une offre."""
    db_offre = crud_offre.get_offre(db, offre_id)
    if not db_offre:
        raise HTTPException(status_code=404, detail="Offre non trouvee")

    updates = _payload_dump(payload, exclude_unset=True)
    if "demande_id" in updates and updates["demande_id"] is not None:
        demande = crud_demande_team_building.get_demande_team_building(db, updates["demande_id"])
        if not demande:
            raise HTTPException(status_code=404, detail="Demande non trouvee")

    return crud_offre.update_offre(
        db,
        db_offre,
        payload,
        updated_by_id=getattr(current_user, "id_utilisateur", None),
    )


@router.delete("/{offre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offre(offre_id: int, db: Session = Depends(get_db)):
    """Supprimer une offre."""
    db_offre = crud_offre.get_offre(db, offre_id)
    if not db_offre:
        raise HTTPException(status_code=404, detail="Offre non trouvee")

    crud_offre.delete_offre(db, db_offre)
