from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import demande_team_building as crud_demande_team_building
from crud import offre as crud_offre
from crud import proforma as crud_proforma
from crud import site as crud_site
from database.schemas import (
    ProformaAssistantMessageCreate,
    ProformaAssistantResponse,
    ProformaAssistantSessionCreate,
    ProformaCreate,
    ProformaRead,
    ProformaUpdate,
)
from security import require_module_access
from services.proforma_assistant import create_assistant_session, handle_assistant_message
from services.proforma_word import WORD_MEDIA_TYPE


router = APIRouter(
    prefix="/api/proformas",
    tags=["proformas"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


def _payload_dump(payload, **kwargs):
    if hasattr(payload, "model_dump"):
        return payload.model_dump(**kwargs)
    return payload.dict(**kwargs)


def _ensure_context_exists(
    db: Session,
    demande_id: int | None = None,
    offre_id: int | None = None,
    site_id: int | None = None,
    demande_tourisme_id: int | None = None,
    demande_tourisme_custom_id: int | None = None,
    offre_tourisme_id: int | None = None,
) -> None:
    if demande_tourisme_id or demande_tourisme_custom_id or offre_tourisme_id:
        raise HTTPException(
            status_code=422,
            detail="Utilisez /api/proformas-tourisme pour les proformas tourisme",
        )
    if demande_id and not crud_demande_team_building.get_demande_team_building(db, demande_id):
        raise HTTPException(status_code=404, detail="Demande team building non trouvée")
    if offre_id and not crud_offre.get_offre(db, offre_id):
        raise HTTPException(status_code=404, detail="Offre non trouvée")
    if site_id and not crud_site.get_site(db, site_id):
        raise HTTPException(status_code=404, detail="Site non trouvé")


def _get_teambuilding_proforma_or_404(db: Session, proforma_id: int):
    db_proforma = crud_proforma.get_proforma(db, proforma_id)
    if not db_proforma or db_proforma.pole != "teambuilding":
        raise HTTPException(status_code=404, detail="Proforma non trouvée")
    return db_proforma


@router.post("/sessions", response_model=ProformaAssistantResponse)
def create_session(
    payload: ProformaAssistantSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    _ensure_context_exists(db, demande_id=payload.demande_id, offre_id=payload.offre_id)
    return create_assistant_session(
        db,
        user_id=getattr(current_user, "id_utilisateur", None),
        demande_id=payload.demande_id,
        offre_id=payload.offre_id,
    )


@router.post("/sessions/{session_id}/messages", response_model=ProformaAssistantResponse)
def post_session_message(
    session_id: str,
    payload: ProformaAssistantMessageCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    try:
        return handle_assistant_message(
            db,
            session_id=session_id,
            message=payload.message,
            user_id=getattr(current_user, "id_utilisateur", None),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get("", response_model=List[ProformaRead])
def list_proformas(
    skip: int = 0,
    limit: int = 100,
    demande_id: int | None = None,
    db: Session = Depends(get_db),
):
    if demande_id:
        return crud_proforma.get_proformas_by_demande(db, demande_id, skip=skip, limit=limit)
    return crud_proforma.get_proformas(db, skip=skip, limit=limit, pole="teambuilding")


@router.get("/{proforma_id}", response_model=ProformaRead)
def get_proforma(proforma_id: int, db: Session = Depends(get_db)):
    return _get_teambuilding_proforma_or_404(db, proforma_id)


@router.post("", response_model=ProformaRead, status_code=status.HTTP_201_CREATED)
def create_proforma(
    payload: ProformaCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    _ensure_context_exists(
        db,
        demande_id=payload.demande_team_building_id,
        offre_id=payload.offre_id,
        site_id=payload.site_id,
        demande_tourisme_id=payload.demande_tourisme_id,
        demande_tourisme_custom_id=payload.demande_tourisme_custom_id,
        offre_tourisme_id=payload.offre_tourisme_id,
    )
    try:
        values = _payload_dump(payload)
        values["pole"] = "teambuilding"
        return crud_proforma.create_proforma(
            db,
            ProformaCreate(**values),
            created_by_id=getattr(current_user, "id_utilisateur", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{proforma_id}/generate-pdf", response_model=ProformaRead)
def generate_pdf(proforma_id: int, db: Session = Depends(get_db)):
    db_proforma = _get_teambuilding_proforma_or_404(db, proforma_id)
    if db_proforma.statut == "annulee":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Proforma annulee")
    try:
        return crud_proforma.generate_pdf_for_proforma(db, db_proforma)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{proforma_id}/generate-word")
def generate_word(proforma_id: int, db: Session = Depends(get_db)):
    db_proforma = _get_teambuilding_proforma_or_404(db, proforma_id)
    if db_proforma.statut == "annulee":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Proforma annulee")
    try:
        word_path = crud_proforma.generate_word_for_proforma(db_proforma)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return FileResponse(
        path=Path(word_path),
        media_type=WORD_MEDIA_TYPE,
        filename=crud_proforma.get_download_filename(db_proforma, "docx"),
    )


@router.get("/{proforma_id}/download")
def download_pdf(proforma_id: int, db: Session = Depends(get_db)):
    db_proforma = _get_teambuilding_proforma_or_404(db, proforma_id)
    pdf_path = crud_proforma.get_pdf_path(db_proforma)
    if not pdf_path or not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="PDF non généré")
    return FileResponse(
        path=Path(pdf_path),
        media_type="application/pdf",
        filename=crud_proforma.get_download_filename(db_proforma, "pdf"),
    )


@router.get("/{proforma_id}/download/word")
def download_word(proforma_id: int, db: Session = Depends(get_db)):
    db_proforma = _get_teambuilding_proforma_or_404(db, proforma_id)
    word_path = crud_proforma.get_word_path(db_proforma)
    if not word_path or not word_path.exists() or not word_path.is_file():
        try:
            word_path = crud_proforma.generate_word_for_proforma(db_proforma)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return FileResponse(
        path=Path(word_path),
        media_type=WORD_MEDIA_TYPE,
        filename=crud_proforma.get_download_filename(db_proforma, "docx"),
    )

@router.put("/{proforma_id}", response_model=ProformaRead)
def update_teambuilding_proforma(
    proforma_id: int,
    payload: ProformaUpdate,
    db: Session = Depends(get_db),
):
    db_proforma = _get_teambuilding_proforma_or_404(db, proforma_id)
    values = _payload_dump(payload, exclude_unset=True)

    _ensure_context_exists(
        db,
        demande_id=values.get("demande_team_building_id", db_proforma.demande_team_building_id),
        offre_id=values.get("offre_id", db_proforma.offre_id),
        site_id=values.get("site_id", db_proforma.site_id),
        demande_tourisme_id=values.get("demande_tourisme_id", db_proforma.demande_tourisme_id),
        demande_tourisme_custom_id=values.get("demande_tourisme_custom_id", db_proforma.demande_tourisme_custom_id),
        offre_tourisme_id=values.get("offre_tourisme_id", db_proforma.offre_tourisme_id),
    )

    values["pole"] = "teambuilding"
    values["demande_tourisme_id"] = None
    values["demande_tourisme_custom_id"] = None
    values["offre_tourisme_id"] = None

    try:
        return crud_proforma.update_proforma(db, db_proforma, values)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
