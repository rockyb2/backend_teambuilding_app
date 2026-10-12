from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session, selectinload

from database.models import Activite, Depense, Facture, Offre, Paiement, Proforma
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


def _line_key(section_index: int, line_index: int) -> str:
    return f"section-{section_index + 1}-ligne-{line_index + 1}"


def _snapshot_sections(snapshot: dict | None) -> list[dict]:
    sections = deepcopy((snapshot or {}).get("sections") or [])
    normalized = []
    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            continue
        lines = []
        for line_index, line in enumerate(section.get("prestations") or section.get("lignes") or []):
            if not isinstance(line, dict) or not str(line.get("designation") or "").strip():
                continue
            current = dict(line)
            current["cle"] = str(current.get("cle") or _line_key(section_index, line_index))
            explicit_amount = current.get("montant_ht")
            if explicit_amount in (None, ""):
                days = _decimal(current.get("nombre_jours", current.get("duree_jours", 1)) or 1)
                quantity = _decimal(current.get("quantite", 1) or 1)
                explicit_amount = days * quantity * _decimal(current.get("prix_unitaire"))
            current["montant_ht"] = float(_decimal(explicit_amount))
            lines.append(current)
        if lines:
            normalized.append({
                "nom": str(section.get("nom") or section.get("name") or "Prestations"),
                "prestations": lines,
            })
    return normalized


def build_proforma_snapshot(proforma: Proforma) -> dict:
    snapshot = {
        "reference": proforma.reference,
        "date_proforma": proforma.date_proforma,
        "sections": proforma.sections or [],
        "sous_total_ht": proforma.sous_total_ht,
        "frais_agence": proforma.frais_agence,
        "tva_frais_agence": proforma.tva_frais_agence,
        "total_ttc": proforma.total_ttc,
    }
    snapshot["sections"] = _snapshot_sections(snapshot)
    return jsonable_encoder(snapshot)


def get_facture_lines(db_facture: Facture) -> list[dict]:
    return [
        {
            **line,
            "section": section["nom"],
        }
        for section in _snapshot_sections(db_facture.proforma_snapshot)
        for line in section["prestations"]
    ]


def get_facture_line_keys(db_facture: Facture) -> set[str]:
    return {line["cle"] for line in get_facture_lines(db_facture)}


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
    if db_facture.frais_agence is not None:
        fees = _decimal(db_facture.frais_agence)
        if not fees.is_finite() or fees < 0 or fees > montant_facture:
            raise ValueError("Les frais d'agence doivent être compris entre zéro et le montant facturé")
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
        raise ValueError("Le montant du paiement doit être supérieur à zéro")

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
    if values.get("proforma_id"):
        if get_active_facture_by_proforma(db, values["proforma_id"]):
            raise ValueError("Une facture active existe deja pour cette proforma")
        proforma = db.get(Proforma, values["proforma_id"])
        if proforma:
            values["proforma_snapshot"] = build_proforma_snapshot(proforma)
            if values.get("frais_agence") is None:
                values["frais_agence"] = proforma.frais_agence

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
        frais_agence=db_proforma.frais_agence,
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
    new_proforma_id = updates.get("proforma_id", db_facture.proforma_id)
    if new_proforma_id:
        existing = get_active_facture_by_proforma(db, new_proforma_id)
        if existing and existing.id != db_facture.id and db_facture.statut != "annulee":
            raise ValueError("Une facture active existe deja pour cette proforma")
        if (new_proforma_id != db_facture.proforma_id and updates.get("frais_agence") is None) or (
            "frais_agence" in updates and updates["frais_agence"] is None
        ):
            proforma = db.get(Proforma, new_proforma_id)
            if proforma:
                updates["frais_agence"] = proforma.frais_agence
    if "proforma_id" in updates and new_proforma_id != db_facture.proforma_id:
        proforma = db.get(Proforma, new_proforma_id) if new_proforma_id else None
        updates["proforma_snapshot"] = build_proforma_snapshot(proforma) if proforma else {}
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


def _facture_expenses(db: Session, db_facture: Facture) -> tuple[list[Depense], list[Depense]]:
    """Return expenses attributable to this invoice/mission exactly once.

    Direct invoice and proforma links have priority. Older mission-level links
    are included only when they are not already assigned to another invoice or
    proforma.
    """
    direct_conditions = [Depense.facture_id == db_facture.id]
    if db_facture.proforma_id:
        direct_conditions.append(and_(
            Depense.facture_id.is_(None),
            Depense.proforma_id == db_facture.proforma_id,
        ))

    mission_conditions = []
    for field in (
        "demande_team_building_id",
        "demande_tourisme_id",
        "demande_tourisme_custom_id",
    ):
        request_id = getattr(db_facture, field)
        if request_id:
            mission_conditions.append(getattr(Depense, field) == request_id)

    if db_facture.pole == "teambuilding":
        offer_ids = set()
        if db_facture.demande_team_building_id:
            offer_ids.update(
                value for (value,) in db.query(Offre.id).filter(
                    Offre.demande_id == db_facture.demande_team_building_id
                ).all()
            )
        proforma = db.get(Proforma, db_facture.proforma_id) if db_facture.proforma_id else None
        if proforma and proforma.offre_id:
            offer_ids.add(proforma.offre_id)
        if offer_ids:
            mission_conditions.append(Depense.offre_id.in_(offer_ids))
        activity_conditions = []
        if offer_ids:
            activity_conditions.append(Activite.offre_id.in_(offer_ids))
        if db_facture.demande_team_building_id:
            activity_conditions.append(Activite.demande_id == db_facture.demande_team_building_id)
        if activity_conditions:
            activity_ids = [
                value for (value,) in db.query(Activite.id).filter(
                    or_(*activity_conditions)
                ).all()
            ]
            if activity_ids:
                mission_conditions.append(Depense.activite_id.in_(activity_ids))

    if mission_conditions:
        direct_conditions.append(and_(
            Depense.facture_id.is_(None),
            Depense.proforma_id.is_(None),
            or_(*mission_conditions),
        ))

    candidates = (
        db.query(Depense)
        .filter(Depense.pole == db_facture.pole, or_(*direct_conditions))
        .order_by(Depense.date_depense.asc().nulls_last(), Depense.id.asc())
        .all()
    )
    multiple_invoice_request = False
    for field in (
        "demande_team_building_id",
        "demande_tourisme_id",
        "demande_tourisme_custom_id",
    ):
        request_id = getattr(db_facture, field)
        if request_id and db.query(Facture).filter(
            Facture.statut != "annulee",
            getattr(Facture, field) == request_id,
        ).count() > 1:
            multiple_invoice_request = True
            break

    if not multiple_invoice_request:
        return candidates, []
    attributable, ambiguous = [], []
    for expense in candidates:
        if expense.facture_id == db_facture.id or (
            db_facture.proforma_id and expense.proforma_id == db_facture.proforma_id
        ):
            attributable.append(expense)
        else:
            ambiguous.append(expense)
    return attributable, ambiguous


def _expense_dict(expense: Depense) -> dict:
    return {
        "id": expense.id,
        "reference": expense.reference,
        "titre": expense.titre,
        "montant": float(_decimal(expense.montant)),
        "date_depense": expense.date_depense,
        "fournisseur": expense.fournisseur,
        "facture_ligne_cle": expense.facture_ligne_cle,
        "justificatif": expense.justificatif,
    }


def get_facture_comparatif(db: Session, db_facture: Facture) -> dict:
    lines = get_facture_lines(db_facture)
    expenses, ambiguous_expenses = _facture_expenses(db, db_facture)
    valid_keys = {line["cle"] for line in lines}
    grouped: dict[str, list[Depense]] = {key: [] for key in valid_keys}
    unassigned = []
    for expense in expenses:
        if expense.facture_ligne_cle in valid_keys:
            grouped[expense.facture_ligne_cle].append(expense)
        else:
            unassigned.append(expense)

    comparison_lines = []
    gain_constate = Decimal("0")
    pending_amount = Decimal("0")
    for line in lines:
        purchases = grouped[line["cle"]]
        billed = _decimal(line["montant_ht"])
        spent = sum((_decimal(expense.montant) for expense in purchases), Decimal("0"))
        if not purchases:
            status = "non_achete"
            variance = None
            pending_amount += billed
        else:
            variance = billed - spent
            gain_constate += variance
            if variance > 0:
                status = "gain"
            elif variance < 0:
                status = "depassement"
            else:
                status = "conforme"
        comparison_lines.append({
            "cle": line["cle"],
            "section": line["section"],
            "designation": line.get("designation"),
            "nombre_jours": line.get("nombre_jours"),
            "quantite": line.get("quantite"),
            "unite": line.get("unite"),
            "prix_unitaire": float(_decimal(line.get("prix_unitaire"))),
            "montant_facture": float(billed),
            "montant_achete": float(spent),
            "ecart": float(variance) if variance is not None else None,
            "statut": status,
            "depenses": [_expense_dict(expense) for expense in purchases],
        })

    unassigned_total = sum((_decimal(expense.montant) for expense in unassigned), Decimal("0"))
    ambiguous_total = sum((_decimal(expense.montant) for expense in ambiguous_expenses), Decimal("0"))
    spent_total = sum((_decimal(expense.montant) for expense in expenses), Decimal("0"))
    agency_fee = _decimal(db_facture.frais_agence)
    observed_result = agency_fee + gain_constate - unassigned_total
    has_breakdown = bool(lines)
    pending_count = sum(line["statut"] == "non_achete" for line in comparison_lines)
    if db_facture.statut == "annulee":
        result_status = "annule"
    elif not has_breakdown:
        result_status = "non_comparable"
    elif db_facture.statut == "payee" and pending_count == 0 and not ambiguous_expenses:
        result_status = "realise"
    else:
        result_status = "provisoire"

    billed_services = sum((_decimal(line["montant_facture"]) for line in comparison_lines), Decimal("0"))
    snapshot_total = _decimal((db_facture.proforma_snapshot or {}).get("total_ttc"))
    invoice_total = _decimal(db_facture.montant_facture)
    return {
        "facture_id": db_facture.id,
        "reference": db_facture.reference_interne,
        "statut_facture": db_facture.statut,
        "proforma_reference": (db_facture.proforma_snapshot or {}).get("reference"),
        "has_breakdown": has_breakdown,
        "result_status": result_status,
        "lignes": comparison_lines,
        "depenses_non_affectees": [_expense_dict(expense) for expense in unassigned],
        "depenses_a_affecter": [_expense_dict(expense) for expense in ambiguous_expenses],
        "resume": {
            "prestations_facturees": float(billed_services),
            "montant_facture": float(invoice_total),
            "total_proforma_snapshot": float(snapshot_total),
            "ecart_facture_proforma": float(invoice_total - snapshot_total) if snapshot_total else 0.0,
            "achats_enregistres": float(spent_total),
            "achats_affectes": float(spent_total - unassigned_total),
            "depenses_non_affectees": float(unassigned_total),
            "depenses_a_affecter": float(ambiguous_total),
            "gain_achats_constate": float(gain_constate),
            "achats_restants_factures": float(pending_amount),
            "frais_agence": float(agency_fee),
            "resultat_constate": float(observed_result),
            "postes_achetes": len(comparison_lines) - pending_count,
            "postes_non_achetes": pending_count,
        },
    }
