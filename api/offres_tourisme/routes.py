from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import demande_tourisme as crud_demande_tourisme
from crud import offre_tourisme as crud_offre_tourisme
from database.schemas import (
    OffreTourismeCreate,
    OffreTourismeRead,
    OffreTourismeUpdate,
)
from security import require_module_access

router = APIRouter(
    prefix="/api/offres-tourisme",
    tags=["offres tourisme"],
    dependencies=[Depends(require_module_access("tourisme"))],
)


def _payload_dump(payload, **kwargs):
    if hasattr(payload, "model_dump"):
        return payload.model_dump(**kwargs)
    return payload.dict(**kwargs)


def _validate_target(
    db: Session,
    demande_tourisme_id: int | None,
    demande_tourisme_custom_id: int | None,
) -> None:
    if (demande_tourisme_id is None) == (demande_tourisme_custom_id is None):
        raise HTTPException(
            status_code=422,
            detail="Une offre tourisme doit etre liee a une seule demande",
        )

    if demande_tourisme_id is not None:
        if not crud_demande_tourisme.get_demande_tourisme(db, demande_tourisme_id):
            raise HTTPException(status_code=404, detail="Demande tourisme non trouvee")
        return

    if not crud_demande_tourisme.get_demande_tourisme_custom(
        db,
        demande_tourisme_custom_id,
    ):
        raise HTTPException(
            status_code=404,
            detail="Demande tourisme personnalisee non trouvee",
        )


@router.get("", response_model=List[OffreTourismeRead])
def get_offres_tourisme(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud_offre_tourisme.get_offres_tourisme(db, skip=skip, limit=limit)


@router.get("/{offre_id}", response_model=OffreTourismeRead)
def get_offre_tourisme(offre_id: int, db: Session = Depends(get_db)):
    db_offre = crud_offre_tourisme.get_offre_tourisme(db, offre_id)
    if not db_offre:
        raise HTTPException(status_code=404, detail="Offre tourisme non trouvee")
    return db_offre


@router.post("", response_model=OffreTourismeRead, status_code=status.HTTP_201_CREATED)
def create_offre_tourisme(
    payload: OffreTourismeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    _validate_target(
        db,
        payload.demande_tourisme_id,
        payload.demande_tourisme_custom_id,
    )
    return crud_offre_tourisme.create_offre_tourisme(
        db,
        payload,
        created_by_id=getattr(current_user, "id_utilisateur", None),
    )


@router.put("/{offre_id}", response_model=OffreTourismeRead)
def update_offre_tourisme(
    offre_id: int,
    payload: OffreTourismeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    db_offre = crud_offre_tourisme.get_offre_tourisme(db, offre_id)
    if not db_offre:
        raise HTTPException(status_code=404, detail="Offre tourisme non trouvee")

    updates = _payload_dump(payload, exclude_unset=True)
    _validate_target(
        db,
        updates.get("demande_tourisme_id", db_offre.demande_tourisme_id),
        updates.get(
            "demande_tourisme_custom_id",
            db_offre.demande_tourisme_custom_id,
        ),
    )
    return crud_offre_tourisme.update_offre_tourisme(
        db,
        db_offre,
        payload,
        updated_by_id=getattr(current_user, "id_utilisateur", None),
    )


@router.delete("/{offre_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offre_tourisme(
    offre_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    db_offre = crud_offre_tourisme.get_offre_tourisme(db, offre_id)
    if not db_offre:
        raise HTTPException(status_code=404, detail="Offre tourisme non trouvee")
    crud_offre_tourisme.delete_offre_tourisme(
        db,
        db_offre,
        utilisateur_id=getattr(current_user, "id_utilisateur", None),
    )
