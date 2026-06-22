from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import demande_tourisme as crud_demande_tourisme
from crud import offre_tourisme as crud_offre_tourisme
from crud import proforma as crud_proforma
from database.schemas import ProformaCreate, ProformaRead
from security import require_module_access


router = APIRouter(
    prefix="/api/proformas-tourisme",
    tags=["proformas tourisme"],
    dependencies=[Depends(require_module_access("tourisme"))],
)


def _payload_dump(payload, **kwargs):
    if hasattr(payload, "model_dump"):
        return payload.model_dump(**kwargs)
    return payload.dict(**kwargs)


def _get_tourism_proforma_or_404(db: Session, proforma_id: int):
    db_proforma = crud_proforma.get_proforma(db, proforma_id)
    if not db_proforma or db_proforma.pole != "tourisme":
        raise HTTPException(status_code=404, detail="Proforma tourisme non trouvee")
    return db_proforma


def _validate_tourism_context(db: Session, values: dict) -> dict:
    if values.get("demande_team_building_id") or values.get("offre_id"):
        raise HTTPException(
            status_code=422,
            detail="Une proforma tourisme ne peut pas etre liee a une demande ou offre team building",
        )

    values["pole"] = "tourisme"
    values["demande_team_building_id"] = None
    values["offre_id"] = None

    offre_tourisme_id = values.get("offre_tourisme_id")
    if offre_tourisme_id:
        offre = crud_offre_tourisme.get_offre_tourisme(db, offre_tourisme_id)
        if not offre:
            raise HTTPException(status_code=404, detail="Offre tourisme non trouvee")

        demande_tourisme_id = values.get("demande_tourisme_id")
        demande_tourisme_custom_id = values.get("demande_tourisme_custom_id")
        if demande_tourisme_id and demande_tourisme_id != offre.demande_tourisme_id:
            raise HTTPException(status_code=422, detail="La demande ne correspond pas a l'offre tourisme")
        if (
            demande_tourisme_custom_id
            and demande_tourisme_custom_id != offre.demande_tourisme_custom_id
        ):
            raise HTTPException(status_code=422, detail="La demande ne correspond pas a l'offre tourisme")

        values["demande_tourisme_id"] = offre.demande_tourisme_id
        values["demande_tourisme_custom_id"] = offre.demande_tourisme_custom_id
        return values

    demande_tourisme_id = values.get("demande_tourisme_id")
    demande_tourisme_custom_id = values.get("demande_tourisme_custom_id")
    if (demande_tourisme_id is None) == (demande_tourisme_custom_id is None):
        raise HTTPException(
            status_code=422,
            detail="Une proforma tourisme doit etre liee a une seule demande tourisme ou a une offre",
        )

    if demande_tourisme_id is not None:
        if not crud_demande_tourisme.get_demande_tourisme(db, demande_tourisme_id):
            raise HTTPException(status_code=404, detail="Demande tourisme non trouvee")
        return values

    if not crud_demande_tourisme.get_demande_tourisme_custom(db, demande_tourisme_custom_id):
        raise HTTPException(status_code=404, detail="Demande tourisme personnalisee non trouvee")
    return values


@router.get("", response_model=List[ProformaRead])
def list_proformas_tourisme(
    skip: int = 0,
    limit: int = 100,
    demande_tourisme_id: int | None = None,
    demande_tourisme_custom_id: int | None = None,
    offre_tourisme_id: int | None = None,
    db: Session = Depends(get_db),
):
    return crud_proforma.get_proformas_by_tourisme_context(
        db,
        demande_tourisme_id=demande_tourisme_id,
        demande_tourisme_custom_id=demande_tourisme_custom_id,
        offre_tourisme_id=offre_tourisme_id,
        skip=skip,
        limit=limit,
    )


@router.get("/{proforma_id}", response_model=ProformaRead)
def get_proforma_tourisme(proforma_id: int, db: Session = Depends(get_db)):
    return _get_tourism_proforma_or_404(db, proforma_id)


@router.post("", response_model=ProformaRead, status_code=status.HTTP_201_CREATED)
def create_proforma_tourisme(
    payload: ProformaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    values = _validate_tourism_context(db, _payload_dump(payload))
    try:
        return crud_proforma.create_proforma(
            db,
            ProformaCreate(**values),
            created_by_id=getattr(current_user, "id_utilisateur", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/offres/{offre_id}", response_model=ProformaRead, status_code=status.HTTP_201_CREATED)
def create_proforma_tourisme_from_offre(
    offre_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    offre = crud_offre_tourisme.get_offre_tourisme(db, offre_id)
    if not offre:
        raise HTTPException(status_code=404, detail="Offre tourisme non trouvee")
    try:
        return crud_proforma.create_tourism_proforma_from_offer(
            db,
            offre,
            created_by_id=getattr(current_user, "id_utilisateur", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{proforma_id}/generate-pdf", response_model=ProformaRead)
def generate_pdf_tourisme(proforma_id: int, db: Session = Depends(get_db)):
    db_proforma = _get_tourism_proforma_or_404(db, proforma_id)
    if db_proforma.statut == "annulee":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Proforma annulee")
    try:
        return crud_proforma.generate_pdf_for_proforma(db, db_proforma)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/{proforma_id}/download")
def download_pdf_tourisme(proforma_id: int, db: Session = Depends(get_db)):
    db_proforma = _get_tourism_proforma_or_404(db, proforma_id)
    pdf_path = crud_proforma.get_pdf_path(db_proforma)
    if not pdf_path or not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="PDF non genere")
    return FileResponse(
        path=Path(pdf_path),
        media_type="application/pdf",
        filename=f"{db_proforma.reference}.pdf",
    )
