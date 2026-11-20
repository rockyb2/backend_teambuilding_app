from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import budget as crud_budget
from crud import offre_tourisme as crud_offre_tourisme
from crud import proforma as crud_proforma
from database.schemas import BudgetCreate, BudgetRead, BudgetUpdate, BudgetValidation
from security import require_module_access


router = APIRouter(
    prefix="/api/budgets-tourisme",
    tags=["budgets tourisme"],
    dependencies=[Depends(require_module_access("tourisme"))],
)


def _dump(payload, **kwargs):
    return payload.model_dump(**kwargs) if hasattr(payload, "model_dump") else payload.dict(**kwargs)


def _get_or_404(db: Session, budget_id: int):
    budget = crud_budget.get_budget(db, budget_id)
    if not budget or budget.pole != "tourisme":
        raise HTTPException(status_code=404, detail="Budget tourisme non trouvé")
    return budget


def _validate_context(db: Session, values: dict) -> dict:
    offre_id = values.get("offre_tourisme_id")
    if not offre_id:
        raise HTTPException(status_code=422, detail="L'offre tourisme est obligatoire")
    offre = crud_offre_tourisme.get_offre_tourisme(db, int(offre_id))
    if not offre:
        raise HTTPException(status_code=404, detail="Offre tourisme non trouvée")
    values.update({
        "pole": "tourisme",
        "offre_id": None,
        "demande_team_building_id": None,
        "site_id": None,
        "demande_tourisme_id": offre.demande_tourisme_id,
        "demande_tourisme_custom_id": offre.demande_tourisme_custom_id,
    })
    return values


@router.get("", response_model=List[BudgetRead])
def list_budgets(offre_tourisme_id: int | None = None, statut: str | None = None, skip: int = 0, limit: int = 1000, db: Session = Depends(get_db)):
    return crud_budget.get_budgets(db, skip=skip, limit=limit, offre_tourisme_id=offre_tourisme_id, statut=statut, pole="tourisme")


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def create_budget(payload: BudgetCreate, db: Session = Depends(get_db), current_user=Depends(require_module_access("tourisme"))):
    values = _validate_context(db, _dump(payload))
    try:
        return crud_budget.create_budget(db, BudgetCreate(**values), getattr(current_user, "id_utilisateur", None))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.put("/{budget_id}", response_model=BudgetRead)
def update_budget(budget_id: int, payload: BudgetUpdate, db: Session = Depends(get_db)):
    budget = _get_or_404(db, budget_id)
    try:
        return crud_budget.update_budget(db, budget, payload)
    except crud_budget.BudgetConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{budget_id}/generate-documents", response_model=BudgetRead)
def generate_documents(budget_id: int, db: Session = Depends(get_db)):
    try:
        return crud_budget.generate_documents_for_budget(db, _get_or_404(db, budget_id))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{budget_id}/valider", response_model=BudgetRead)
def validate_budget(budget_id: int, payload: BudgetValidation | None = None, db: Session = Depends(get_db)):
    try:
        return crud_budget.validate_budget(db, _get_or_404(db, budget_id), payload.remplacer_budget_id if payload else None)
    except crud_budget.BudgetConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{budget_id}/proforma-draft")
def proforma_draft(budget_id: int, db: Session = Depends(get_db)):
    _get_or_404(db, budget_id)
    try:
        return crud_proforma.build_proforma_from_budget(db, budget_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_budget(budget_id: int, db: Session = Depends(get_db)):
    crud_budget.cancel_budget(db, _get_or_404(db, budget_id))


@router.get("/{budget_id}/download/pdf")
def download_pdf(budget_id: int, db: Session = Depends(get_db)):
    budget = _get_or_404(db, budget_id)
    path = crud_budget.get_budget_pdf_path(budget)
    if not path or not path.is_file() or not crud_budget.is_budget_pdf_current(path):
        crud_budget.generate_documents_for_budget(db, budget)
        path = crud_budget.get_budget_pdf_path(budget)
    if not path or not path.is_file():
        raise HTTPException(status_code=404, detail="PDF non généré")
    return FileResponse(path=Path(path), media_type="application/pdf", filename=f"{budget.reference}.pdf")


@router.get("/{budget_id}/download/excel")
def download_excel(budget_id: int, db: Session = Depends(get_db)):
    budget = _get_or_404(db, budget_id)
    crud_budget.generate_excel_for_budget(db, budget)
    db.commit()
    path = crud_budget.get_budget_excel_path(budget)
    if not path or not path.is_file():
        raise HTTPException(status_code=404, detail="Excel non généré")
    return FileResponse(path=Path(path), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=f"{budget.reference}.xlsx")
