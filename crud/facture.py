from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session, selectinload

from database.models import Facture, Paiement, Proforma
from database.schemas import FactureCreate, FactureUpdate, PaiementCreate, PaiementUpdate


FACTURE_REFERENCE_PREFIX = "FAC"
NON_NULL_FACTURE_FIELDS = {"pole", "client", "date_facture", "montant_facture"}
NON_NULL_PAIEMENT_FIELDS = {"montant", "date_paiement"}


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def _decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def get_facture(db: Session, facture_id: int) -> Optional[Facture]:
    return (
        db.query(Facture)
        .options(selectinload(Facture.paiements))
        .filter(Facture.id == facture_id)
        .first()
    )


def get_facture_by_reference(db: Session, reference_interne: str) -> Optional[Facture]:
    return (
        db.query(Facture)
        .options(selectinload(Facture.paiements))
        .filter(Facture.reference_interne == reference_interne)
        .first()
    )


def get_active_facture_by_proforma(db: Session, proforma_id: int) -> Optional[Facture]:
    return (
        db.query(Facture)
        .options(selectinload(Facture.paiements))
        .filter(Facture.proforma_id == proforma_id, Facture.statut != "annulee")
        .first()
    )


def get_factures(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    pole: str | None = None,
    statut: str | None = None,
) -> list[Facture]:
    query = db.query(Facture).options(selectinload(Facture.paiements))
    if pole:
        query = query.filter(Facture.pole == pole)
    if statut:
        query = query.filter(Facture.statut == statut)
    return query.order_by(Facture.date_facture.desc(), Facture.id.desc()).offset(skip).limit(limit).all()


def generate_facture_reference(db: Session, created_at: datetime | None = None) -> str:
    reference_date = created_at or datetime.now()
    year_key = reference_date.strftime("%Y")
    prefix = f"{FACTURE_REFERENCE_PREFIX}-{year_key}-"

    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"facture-reference-{year_key}"},
        )

    references = db.query(Facture.reference_interne).filter(Facture.reference_interne.like(f"{prefix}%")).all()
    highest_rank = 0
    for (reference,) in references:
        suffix = reference.removeprefix(prefix) if reference else ""
        if suffix.isdigit():
            highest_rank = max(highest_rank, int(suffix))

    return f"{prefix}{highest_rank + 1:04d}"


def _payments_total(db: Session, facture_id: int, exclude_paiement_id: int | None = None) -> Decimal:
    query = db.query(func.coalesce(func.sum(Paiement.montant), 0)).filter(Paiement.facture_id == facture_id)
    if exclude_paiement_id is not None:
        query = query.filter(Paiement.id != exclude_paiement_id)
    return _decimal(query.scalar())


def _sync_facture_statut(db: Session, db_facture: Facture) -> None:
    if db_facture.statut == "annulee":
        return

    total_paye = _payments_total(db, db_facture.id)
    montant_facture = _decimal(db_facture.montant_facture)

    if total_paye <= 0:
        db_facture.statut = "non_payee"
    elif total_paye < montant_facture:
        db_facture.statut = "partiellement_payee"
    else:
        db_facture.statut = "payee"


def _ensure_valid_facture_amount(db: Session, db_facture: Facture) -> None:
    montant_facture = _decimal(db_facture.montant_facture)
    if montant_facture < 0:
        raise ValueError("Le montant de la facture ne peut pas etre negatif")
    if db_facture.id is None or db_facture.statut == "annulee":
        return
    total_paye = _payments_total(db, db_facture.id)
    if total_paye > montant_facture:
        raise ValueError("Le montant de la facture est inferieur aux paiements deja enregistres")


def _ensure_required_values(updates: dict, required_fields: set[str]) -> None:
    null_fields = [field for field in required_fields if field in updates and updates[field] is None]
    if null_fields:
        raise ValueError(f"Champs obligatoires invalides: {', '.join(sorted(null_fields))}")


def _ensure_paiement_allowed(
    db: Session,
    db_facture: Facture,
    montant: Decimal,
    exclude_paiement_id: int | None = None,
) -> None:
    if db_facture.statut == "annulee":
        raise ValueError("Impossible d'ajouter un paiement sur une facture annulee")
    if montant <= 0:
        raise ValueError("Le montant du paiement doit etre superieur a zero")

    total_hors_paiement = _payments_total(db, db_facture.id, exclude_paiement_id=exclude_paiement_id)
    if total_hors_paiement + montant > _decimal(db_facture.montant_facture):
        raise ValueError("Le total des paiements depasse le montant de la facture")


def create_facture(
    db: Session,
    payload: FactureCreate,
    created_by_id: int | None = None,
) -> Facture:
    values = _model_dump(payload)
    values["date_facture"] = values.get("date_facture") or date.today()
    _ensure_required_values(values, NON_NULL_FACTURE_FIELDS)
    values["reference_interne"] = generate_facture_reference(db)
    values["statut"] = "non_payee"
    values["created_by_id"] = created_by_id
    values["updated_by_id"] = created_by_id

    db_facture = Facture(**values)
    _ensure_valid_facture_amount(db, db_facture)
    db.add(db_facture)
    db.commit()
    db.refresh(db_facture)
    return get_facture(db, db_facture.id) or db_facture


def create_facture_from_proforma(
    db: Session,
    db_proforma: Proforma,
    created_by_id: int | None = None,
) -> Facture:
    if db_proforma.statut == "annulee":
        raise ValueError("Impossible de creer une facture depuis une proforma annulee")
    if get_active_facture_by_proforma(db, db_proforma.id):
        raise ValueError("Une facture active existe deja pour cette proforma")

    payload = FactureCreate(
        pole=db_proforma.pole,
        proforma_id=db_proforma.id,
        demande_team_building_id=db_proforma.demande_team_building_id,
        demande_tourisme_id=db_proforma.demande_tourisme_id,
        demande_tourisme_custom_id=db_proforma.demande_tourisme_custom_id,
        client=db_proforma.client,
        objet=db_proforma.objet,
        date_facture=date.today(),
        montant_facture=db_proforma.total_ttc,
    )
    return create_facture(db, payload, created_by_id=created_by_id)


def update_facture(
    db: Session,
    db_facture: Facture,
    payload: FactureUpdate | dict,
    updated_by_id: int | None = None,
) -> Facture:
    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    requested_status = updates.pop("statut", None)
    if requested_status is not None and requested_status != db_facture.statut:
        raise ValueError("Le statut de la facture est calcule automatiquement; utilisez l'annulation dediee")
    _ensure_required_values(updates, NON_NULL_FACTURE_FIELDS)
    for key, value in updates.items():
        if hasattr(db_facture, key):
            setattr(db_facture, key, value)

    db_facture.updated_by_id = updated_by_id
    _ensure_valid_facture_amount(db, db_facture)
    _sync_facture_statut(db, db_facture)
    db.commit()
    db.refresh(db_facture)
    return get_facture(db, db_facture.id) or db_facture


def annuler_facture(
    db: Session,
    db_facture: Facture,
    updated_by_id: int | None = None,
) -> Facture:
    if db_facture.statut == "annulee":
        return get_facture(db, db_facture.id) or db_facture
    if _payments_total(db, db_facture.id) > 0:
        raise ValueError("Impossible d'annuler une facture avec des paiements")

    db_facture.statut = "annulee"
    db_facture.updated_by_id = updated_by_id
    db.commit()
    db.refresh(db_facture)
    return get_facture(db, db_facture.id) or db_facture


def get_paiement(db: Session, paiement_id: int) -> Optional[Paiement]:
    return db.query(Paiement).filter(Paiement.id == paiement_id).first()


def get_paiements_by_facture(db: Session, facture_id: int, skip: int = 0, limit: int = 100) -> list[Paiement]:
    return (
        db.query(Paiement)
        .filter(Paiement.facture_id == facture_id)
        .order_by(Paiement.date_paiement.desc(), Paiement.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_paiement(
    db: Session,
    db_facture: Facture,
    payload: PaiementCreate,
    created_by_id: int | None = None,
) -> Paiement:
    values = _model_dump(payload)
    values["facture_id"] = db_facture.id
    values["date_paiement"] = values.get("date_paiement") or date.today()
    _ensure_required_values(values, NON_NULL_PAIEMENT_FIELDS)
    values["created_by_id"] = created_by_id
    values["updated_by_id"] = created_by_id

    _ensure_paiement_allowed(db, db_facture, _decimal(values["montant"]))
    db_paiement = Paiement(**values)
    db.add(db_paiement)
    db.flush()
    _sync_facture_statut(db, db_facture)
    db.commit()
    db.refresh(db_paiement)
    return db_paiement


def update_paiement(
    db: Session,
    db_paiement: Paiement,
    payload: PaiementUpdate | dict,
    updated_by_id: int | None = None,
) -> Paiement:
    db_facture = get_facture(db, db_paiement.facture_id)
    if not db_facture:
        raise ValueError("Facture introuvable pour ce paiement")

    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    _ensure_required_values(updates, NON_NULL_PAIEMENT_FIELDS)
    new_montant = _decimal(updates.get("montant", db_paiement.montant))
    _ensure_paiement_allowed(db, db_facture, new_montant, exclude_paiement_id=db_paiement.id)

    for key, value in updates.items():
        if hasattr(db_paiement, key):
            setattr(db_paiement, key, value)
    db_paiement.updated_by_id = updated_by_id

    db.flush()
    _sync_facture_statut(db, db_facture)
    db.commit()
    db.refresh(db_paiement)
    return db_paiement


def delete_paiement(db: Session, db_paiement: Paiement) -> None:
    db_facture = get_facture(db, db_paiement.facture_id)
    db.delete(db_paiement)
    db.flush()
    if db_facture:
        _sync_facture_statut(db, db_facture)
    db.commit()
