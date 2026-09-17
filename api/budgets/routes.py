from __future__ import annotations

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import budget as crud_budget
from crud import demande_team_building as crud_demande_team_building
from crud import offre as crud_offre
from crud import site as crud_site
from crud import proforma as crud_proforma
from database.schemas import BudgetCreate, BudgetRead, BudgetUpdate, BudgetMultiSiteCreate, BudgetValidation
from security import require_module_access


router = APIRouter(
    prefix="/api/budgets",
    tags=["budgets"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


def _payload_dump(payload, **kwargs):
    if hasattr(payload, "model_dump"):
        return payload.model_dump(**kwargs)
    return payload.dict(**kwargs)


def _get_budget_or_404(db: Session, budget_id: int):
    db_budget = crud_budget.get_budget(db, budget_id)
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget non trouvé")
    return db_budget


def _ensure_context_exists(db: Session, values: dict) -> dict:
    offre_id = values.get("offre_id")
    if not offre_id:
        raise HTTPException(status_code=422, detail="L'offre est obligatoire")

    db_offre = crud_offre.get_offre(db, int(offre_id))
    if not db_offre:
        raise HTTPException(status_code=404, detail="Offre non trouvée")

    demande_id = values.get("demande_team_building_id") or db_offre.demande_id
    if demande_id != db_offre.demande_id:
        raise HTTPException(status_code=422, detail="La demande ne correspond pas à l'offre.")
    if demande_id and not crud_demande_team_building.get_demande_team_building(db, int(demande_id)):
        raise HTTPException(status_code=404, detail="Demande team building non trouvée")

    site_id = values.get("site_id")
    if site_id and not crud_site.get_site(db, int(site_id)):
        raise HTTPException(status_code=404, detail="Site non trouvé")

    values["demande_team_building_id"] = demande_id
    return values


@router.get("", response_model=List[BudgetRead])
def list_budgets(
    skip: int = 0,
    limit: int = 100,
    offre_id: int | None = None,
    statut: str | None = None,
    db: Session = Depends(get_db),
):
    return crud_budget.get_budgets(db, skip=skip, limit=limit, offre_id=offre_id, statut=statut)


@router.get("/{budget_id}", response_model=BudgetRead)
def get_budget(budget_id: int, db: Session = Depends(get_db)):
    return _get_budget_or_404(db, budget_id)


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    values = _ensure_context_exists(db, _payload_dump(payload))
    try:
        return crud_budget.create_budget(
            db,
            BudgetCreate(**values),
            created_by_id=getattr(current_user, "id_utilisateur", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/multi-sites", response_model=List[BudgetRead], status_code=status.HTTP_201_CREATED)
def create_multi_site_budgets(
    payload: BudgetMultiSiteCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    items = [BudgetCreate(**_ensure_context_exists(db, _payload_dump(item))) for item in payload.budgets]
    try:
        return crud_budget.create_multi_site_budgets(db, items, getattr(current_user, "id_utilisateur", None))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{budget_id}/proforma-draft")
def get_proforma_draft(budget_id: int, db: Session = Depends(get_db)):
    _get_budget_or_404(db, budget_id)
    try:
        return crud_proforma.build_proforma_from_budget(db, budget_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/{budget_id}", response_model=BudgetRead)
def update_budget(
    budget_id: int,
    payload: BudgetUpdate,
    db: Session = Depends(get_db),
):
    db_budget = _get_budget_or_404(db, budget_id)
    values = _payload_dump(payload, exclude_unset=True)
    if "offre_id" in values or "demande_team_building_id" in values or "site_id" in values:
        merged = {
            "offre_id": values.get("offre_id", db_budget.offre_id),
            "demande_team_building_id": values.get("demande_team_building_id", db_budget.demande_team_building_id),
            "site_id": values.get("site_id", db_budget.site_id),
        }
        _ensure_context_exists(db, merged)
    try:
        return crud_budget.update_budget(db, db_budget, payload)
    except crud_budget.BudgetConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{budget_id}/generate-documents", response_model=BudgetRead)
def generate_budget_documents(budget_id: int, db: Session = Depends(get_db)):
    db_budget = _get_budget_or_404(db, budget_id)
    if db_budget.statut == "annule":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Budget annulé")
    try:
        return crud_budget.generate_documents_for_budget(db, db_budget)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/{budget_id}/valider", response_model=BudgetRead)
def validate_budget(budget_id: int, payload: BudgetValidation | None = None, db: Session = Depends(get_db)):
    db_budget = _get_budget_or_404(db, budget_id)
    if db_budget.statut == "annule":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Budget annulé")
    try:
        return crud_budget.validate_budget(db, db_budget, payload.remplacer_budget_id if payload else None)
    except crud_budget.BudgetConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_budget(budget_id: int, db: Session = Depends(get_db)):
    db_budget = _get_budget_or_404(db, budget_id)
    crud_budget.cancel_budget(db, db_budget)


@router.get("/{budget_id}/download/pdf")
def download_budget_pdf(budget_id: int, db: Session = Depends(get_db)):
    db_budget = _get_budget_or_404(db, budget_id)
    pdf_path = crud_budget.get_budget_pdf_path(db_budget)
    if not pdf_path or not pdf_path.exists() or not pdf_path.is_file():
        raise HTTPException(status_code=404, detail="PDF non généré")
    return FileResponse(
        path=Path(pdf_path),
        media_type="application/pdf",
        filename=f"{db_budget.reference}.pdf",
    )


@router.get("/{budget_id}/download/excel")
def download_budget_excel(budget_id: int, db: Session = Depends(get_db)):
    db_budget = _get_budget_or_404(db, budget_id)
    crud_budget.lock_offer(db, db_budget.offre_id)
    db.refresh(db_budget)
    if db_budget.statut == "annule":
        raise HTTPException(status_code=409, detail="Budget annulé")
    try:
        crud_budget.generate_excel_for_budget(db, db_budget)
        db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    excel_path = crud_budget.get_budget_excel_path(db_budget)
    if not excel_path or not excel_path.exists() or not excel_path.is_file():
        raise HTTPException(status_code=404, detail="Excel non généré")
    return FileResponse(
        path=Path(excel_path),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"{db_budget.groupe_reference or db_budget.reference}.xlsx",
    )
