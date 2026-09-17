from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from database.models import Budget, Offre
from database.schemas import BudgetCreate, BudgetUpdate
from services.budget_documents import (
    BASE_DIR, calculate_budget_totals, generate_budget_excel, generate_budget_pdf,
    generate_multi_site_budget_excel,
)


BUDGET_REFERENCE_PREFIX = "BUD"


class BudgetConflict(ValueError):
    pass


def lock_offer(db: Session, offre_id: int) -> Offre:
    offer = db.query(Offre).filter(Offre.id == offre_id).with_for_update().populate_existing().first()
    if not offer:
        raise ValueError("Offre non trouvée.")
    return offer


def _model_dump(schema_obj, **kwargs):
    if isinstance(schema_obj, dict):
        return dict(schema_obj)
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def _relative_backend_path(path: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(BASE_DIR)).replace("\\", "/")
    except ValueError:
        return str(path)


def _absolute_backend_path(path: str | None) -> Path | None:
    if not path:
        return None
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return (BASE_DIR / candidate).resolve()


def get_budget(db: Session, budget_id: int) -> Optional[Budget]:
    return db.query(Budget).filter(Budget.id == budget_id).first()


def get_budgets(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    offre_id: int | None = None,
    statut: str | None = None,
) -> list[Budget]:
    query = db.query(Budget)
    if offre_id is not None:
        query = query.filter(Budget.offre_id == offre_id)
    if statut:
        query = query.filter(Budget.statut == statut)
    return query.order_by(Budget.created_at.desc()).offset(skip).limit(limit).all()


def generate_budget_reference(db: Session, created_at: datetime | None = None) -> str:
    reference_date = created_at or datetime.now()
    year_key = reference_date.strftime("%Y")
    prefix = f"{BUDGET_REFERENCE_PREFIX}-{year_key}-"

    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"budget-reference-{year_key}"},
        )

    references = db.query(Budget.reference).filter(Budget.reference.like(f"{prefix}%")).all()
    highest_rank = 0
    for (reference,) in references:
        suffix = reference.removeprefix(prefix) if reference else ""
        if suffix.isdigit():
            highest_rank = max(highest_rank, int(suffix))

    return f"{prefix}{highest_rank + 1:04d}"


def _prepare_values(values: dict) -> dict:
    values["date_budget"] = values.get("date_budget") or date.today()
    totals = calculate_budget_totals(
        values.get("sections") or [],
        values.get("frais_agence") or 0,
        values.get("taux_tva_frais_agence") or 0,
        values.get("mode_frais_agence") or "montant",
    )
    values["sections"] = totals["sections"]
    values["frais_agence"] = totals["frais_agence"]
    values["mode_frais_agence"] = totals["mode_frais_agence"]
    values["taux_tva_frais_agence"] = totals["taux_tva_frais_agence"]
    values["sous_total_ht"] = totals["sous_total_ht"]
    values["tva_frais_agence"] = totals["tva_frais_agence"]
    values["total_ht"] = totals["total_ht"]
    values["total_ttc"] = totals["total_ttc"]
    values["options_selectionnees"] = values.get("options_selectionnees") or {}
    return values


def sync_offer_montant_from_validated_budgets(db: Session, offre_id: int | None) -> None:
    if offre_id is None:
        return
    total = (
        db.query(Budget.total_ttc)
        .filter(Budget.offre_id == offre_id, Budget.statut == "valide")
        .scalar()
    )
    db_offre = db.query(Offre).filter(Offre.id == offre_id).first()
    if db_offre:
        db_offre.montant_total = Decimal(str(total or 0))


def create_budget(
    db: Session,
    payload: BudgetCreate,
    created_by_id: int | None = None,
    *,
    commit: bool = True,
    groupe_reference: str | None = None,
) -> Budget:
    values = _prepare_values(_model_dump(payload))
    if values.get("statut") == "valide":
        raise ValueError("Utilisez l'action Valider pour retenir un budget.")
    lock_offer(db, values["offre_id"])
    values["groupe_reference"] = groupe_reference
    values["reference"] = generate_budget_reference(db)
    values["created_by_id"] = created_by_id

    db_budget = Budget(**values)
    db.add(db_budget)
    db.flush()
    if commit:
        db.commit()
        db.refresh(db_budget)
    return db_budget


def update_budget(db: Session, db_budget: Budget, payload: BudgetUpdate | dict) -> Budget:
    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    if updates.get("statut") == "valide":
        raise ValueError("Utilisez l'action Valider pour retenir un budget.")
    old_offre_id = db_budget.offre_id
    if any(key in updates and updates[key] != getattr(db_budget, key) for key in ("offre_id", "site_id", "demande_team_building_id")):
        raise ValueError("Créez un nouveau budget pour changer d'offre, de demande ou de site.")
    lock_offer(db, old_offre_id)
    db.refresh(db_budget)
    if db_budget.statut == "annule":
        raise BudgetConflict("Un budget annulé ne peut plus être modifié.")
    values = {
        column.name: getattr(db_budget, column.name)
        for column in Budget.__table__.columns
        if column.name not in {"id", "reference", "created_at", "updated_at", "created_by_id"}
    }
    values.update(updates)
    if db_budget.statut == "valide" and any(key != "statut" for key in updates):
        values["statut"] = "brouillon"
    values = _prepare_values(values)
    for key, value in values.items():
        if hasattr(db_budget, key):
            setattr(db_budget, key, value)
    db_budget.fichier_pdf = None
    db_budget.fichier_excel = None
    db.flush()
    sync_offer_montant_from_validated_budgets(db, old_offre_id)
    if old_offre_id != db_budget.offre_id:
        sync_offer_montant_from_validated_budgets(db, db_budget.offre_id)
    db.commit()
    db.refresh(db_budget)
    return db_budget


def budget_document_data(db_budget: Budget) -> dict:
    site_name = getattr(db_budget.site, "nom_site", None) if db_budget.site else None
    site_location = getattr(db_budget.site, "localisation", None) if db_budget.site else None
    lieu = " - ".join(part for part in (site_name, site_location) if part) or site_name or site_location
    return {
        "reference": db_budget.reference,
        "offre_id": db_budget.offre_id,
        "site_id": db_budget.site_id,
        "site_nom": site_name,
        "site_localisation": site_location,
        "lieu": lieu,
        "client": db_budget.client,
        "nombre_personnes": db_budget.nombre_personnes,
        "titre": db_budget.titre,
        "date_budget": db_budget.date_budget,
        "date_evenement": db_budget.date_evenement,
        "duree_jours": db_budget.duree_jours,
        "sections": db_budget.sections,
        "frais_agence": db_budget.frais_agence,
        "mode_frais_agence": db_budget.mode_frais_agence,
        "taux_tva_frais_agence": db_budget.taux_tva_frais_agence,
        "modalite_paiement": db_budget.modalite_paiement,
        "notes": db_budget.notes,
        "statut": db_budget.statut,
    }


def generate_excel_for_budget(db: Session, db_budget: Budget) -> str:
    if not db_budget.groupe_reference:
        path = generate_budget_excel(budget_document_data(db_budget))
        db_budget.fichier_excel = _relative_backend_path(path)
        return path
    members = db.query(Budget).filter(Budget.groupe_reference == db_budget.groupe_reference).order_by(Budget.id).all()
    path = generate_multi_site_budget_excel(
        [budget_document_data(member) for member in members], db_budget.groupe_reference,
    )
    for member in members:
        member.fichier_excel = _relative_backend_path(path)
    return path


def create_multi_site_budgets(db: Session, payloads: list[BudgetCreate], created_by_id: int | None = None) -> list[Budget]:
    if not payloads or len({item.offre_id for item in payloads}) != 1:
        raise ValueError("Les budgets doivent appartenir à la même offre.")
    site_ids = [item.site_id for item in payloads]
    if None in site_ids or len(site_ids) != len(set(site_ids)):
        raise ValueError("Sélectionnez des sites distincts pour chaque budget.")
    try:
        lock_offer(db, payloads[0].offre_id)
        group = f"MULTI-{generate_budget_reference(db)}"
        members = [create_budget(db, item, created_by_id, commit=False, groupe_reference=group) for item in payloads]
        for member in members:
            member.fichier_pdf = _relative_backend_path(generate_budget_pdf(budget_document_data(member)))
            member.statut = "genere"
        generate_excel_for_budget(db, members[0])
        db.commit()
        for member in members:
            db.refresh(member)
        return members
    except Exception:
        db.rollback()
        raise


def validate_budget(db: Session, db_budget: Budget, remplacer_budget_id: int | None = None) -> Budget:
    lock_offer(db, db_budget.offre_id)
    db.refresh(db_budget)
    if db_budget.statut == "annule":
        raise BudgetConflict("Budget annulé.")
    current = db.query(Budget).filter(Budget.offre_id == db_budget.offre_id, Budget.statut == "valide").first()
    if current and current.id == db_budget.id:
        return db_budget
    if current and current.id != remplacer_budget_id:
        raise BudgetConflict(f"Le budget {current.reference} est déjà validé. Confirmez son remplacement.")
    if remplacer_budget_id is not None and (not current or current.id != remplacer_budget_id):
        raise BudgetConflict("Le budget retenu a changé. Actualisez la liste avant de valider.")
    if not db_budget.sections:
        raise ValueError("Un budget vide ne peut pas être validé.")
    if current:
        current.statut = "genere"
        db.flush()
    db_budget.statut = "valide"
    db.flush()
    sync_offer_montant_from_validated_budgets(db, db_budget.offre_id)
    db.commit()
    db.refresh(db_budget)
    return db_budget


def generate_documents_for_budget(db: Session, db_budget: Budget) -> Budget:
    lock_offer(db, db_budget.offre_id)
    db.refresh(db_budget)
    if db_budget.statut == "annule":
        raise BudgetConflict("Budget annulé.")
    data = budget_document_data(db_budget)
    pdf_path = generate_budget_pdf(data)
    db_budget.fichier_pdf = _relative_backend_path(pdf_path)
    generate_excel_for_budget(db, db_budget)
    if db_budget.statut == "brouillon":
        db_budget.statut = "genere"
    db.flush()
    db.commit()
    db.refresh(db_budget)
    return db_budget


def get_budget_pdf_path(db_budget: Budget) -> Path | None:
    return _absolute_backend_path(db_budget.fichier_pdf)


def get_budget_excel_path(db_budget: Budget) -> Path | None:
    return _absolute_backend_path(db_budget.fichier_excel)


def cancel_budget(db: Session, db_budget: Budget) -> None:
    lock_offer(db, db_budget.offre_id)
    db.refresh(db_budget)
    db_budget.statut = "annule"
    db.flush()
    sync_offer_montant_from_validated_budgets(db, db_budget.offre_id)
    db.commit()
