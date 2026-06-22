from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from database.models import DemandeTourisme, DemandeTourismeCustom, OffreTourisme, Proforma
from database.schemas import ProformaCreate, ProformaUpdate
from services.proforma_pdf import BASE_DIR, calculate_totals, generate_proforma_pdf


PROFORMA_REFERENCE_PREFIX = "PRO"


def _model_dump(schema_obj, **kwargs):
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


def get_proforma(db: Session, proforma_id: int) -> Optional[Proforma]:
    return db.query(Proforma).filter(Proforma.id == proforma_id).first()


def get_proformas(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    pole: str | None = None,
) -> list[Proforma]:
    query = db.query(Proforma)
    if pole:
        query = query.filter(Proforma.pole == pole)
    return query.order_by(Proforma.created_at.desc()).offset(skip).limit(limit).all()


def get_proformas_by_demande(
    db: Session,
    demande_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Proforma]:
    return (
        db.query(Proforma)
        .filter(Proforma.demande_team_building_id == demande_id)
        .order_by(Proforma.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_proformas_by_tourisme_context(
    db: Session,
    demande_tourisme_id: int | None = None,
    demande_tourisme_custom_id: int | None = None,
    offre_tourisme_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Proforma]:
    query = db.query(Proforma).filter(Proforma.pole == "tourisme")
    if demande_tourisme_id is not None:
        query = query.filter(Proforma.demande_tourisme_id == demande_tourisme_id)
    if demande_tourisme_custom_id is not None:
        query = query.filter(Proforma.demande_tourisme_custom_id == demande_tourisme_custom_id)
    if offre_tourisme_id is not None:
        query = query.filter(Proforma.offre_tourisme_id == offre_tourisme_id)
    return query.order_by(Proforma.created_at.desc()).offset(skip).limit(limit).all()


def generate_proforma_reference(db: Session, created_at: datetime | None = None) -> str:
    reference_date = created_at or datetime.now()
    year_key = reference_date.strftime("%Y")
    prefix = f"{PROFORMA_REFERENCE_PREFIX}-{year_key}-"

    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"proforma-reference-{year_key}"},
        )

    references = (
        db.query(Proforma.reference)
        .filter(Proforma.reference.like(f"{prefix}%"))
        .all()
    )

    highest_rank = 0
    for (reference,) in references:
        suffix = reference.removeprefix(prefix) if reference else ""
        if suffix.isdigit():
            highest_rank = max(highest_rank, int(suffix))

    return f"{prefix}{highest_rank + 1:04d}"


def _prepare_values(values: dict) -> dict:
    totals = calculate_totals(
        values.get("sections") or [],
        values.get("frais_agence") or 0,
        values.get("taux_tva_frais_agence") or 18,
    )
    values["sections"] = totals["sections"]
    values["frais_agence"] = totals["frais_agence"]
    values["sous_total_ht"] = totals["sous_total_ht"]
    values["tva_frais_agence"] = totals["tva_frais_agence"]
    values["total_ttc"] = totals["total_ttc"]
    values["details_frais_agence"] = values.get("details_frais_agence") or []
    values["recommandations"] = values.get("recommandations") or []
    return values


def create_proforma(
    db: Session,
    payload: ProformaCreate,
    created_by_id: int | None = None,
) -> Proforma:
    values = _prepare_values(_model_dump(payload))
    values["reference"] = generate_proforma_reference(db)
    values["created_by_id"] = created_by_id

    db_proforma = Proforma(**values)
    db.add(db_proforma)
    db.commit()
    db.refresh(db_proforma)
    return db_proforma


def _tourisme_client_name(demande: DemandeTourisme | DemandeTourismeCustom | None) -> str:
    if isinstance(demande, DemandeTourisme):
        values = (demande.prenom, demande.nom)
    elif isinstance(demande, DemandeTourismeCustom):
        values = (demande.prenoms_client, demande.nom_client)
    else:
        values = ()
    name = " ".join(value.strip() for value in values if value and value.strip())
    return name or "Client tourisme"


def _tourisme_people_count(demande: DemandeTourisme | DemandeTourismeCustom | None) -> int:
    if isinstance(demande, DemandeTourisme):
        return max(int(demande.nombre_voyageurs or 1), 1)
    if isinstance(demande, DemandeTourismeCustom):
        return max(int(demande.nombre_personne or 1), 1)
    return 1


def _tourisme_event_date(demande: DemandeTourisme | DemandeTourismeCustom | None):
    if isinstance(demande, DemandeTourisme):
        return demande.date_depart_souhaitee
    return None


def build_tourism_proforma_values(db_offre: OffreTourisme) -> dict:
    demande = db_offre.demande_tourisme or db_offre.demande_tourisme_custom
    amount = db_offre.montant_total or 0
    title = db_offre.titre or "Prestation touristique"
    return {
        "pole": "tourisme",
        "demande_team_building_id": None,
        "offre_id": None,
        "demande_tourisme_id": db_offre.demande_tourisme_id,
        "demande_tourisme_custom_id": db_offre.demande_tourisme_custom_id,
        "offre_tourisme_id": db_offre.id,
        "site_id": None,
        "client": _tourisme_client_name(demande),
        "nombre_personnes": _tourisme_people_count(demande),
        "objet": title,
        "date_proforma": date.today(),
        "date_evenement": _tourisme_event_date(demande),
        "sections": [
            {
                "nom": "Prestations touristiques",
                "prestations": [
                    {
                        "designation": title,
                        "nombre_jours": 1,
                        "quantite": 1,
                        "prix_unitaire": amount,
                    }
                ],
            }
        ],
        "frais_agence": 0,
        "details_frais_agence": [],
        "taux_tva_frais_agence": 18,
        "modalite_paiement": db_offre.conditions_paiement,
        "recommandations": [],
        "notes": db_offre.observations,
        "statut": "brouillon",
    }


def create_tourism_proforma_from_offer(
    db: Session,
    db_offre: OffreTourisme,
    created_by_id: int | None = None,
) -> Proforma:
    values = _prepare_values(build_tourism_proforma_values(db_offre))
    values["reference"] = generate_proforma_reference(db)
    values["created_by_id"] = created_by_id

    db_proforma = Proforma(**values)
    db.add(db_proforma)
    db.commit()
    db.refresh(db_proforma)
    return db_proforma


def update_proforma(db: Session, db_proforma: Proforma, payload: ProformaUpdate | dict) -> Proforma:
    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    values = {
        column.name: getattr(db_proforma, column.name)
        for column in Proforma.__table__.columns
        if column.name not in {"id", "reference", "created_at", "updated_at", "created_by_id"}
    }
    values.update(updates)
    values = _prepare_values(values)
    for key, value in values.items():
        if hasattr(db_proforma, key):
            setattr(db_proforma, key, value)
    db.commit()
    db.refresh(db_proforma)
    return db_proforma


def generate_pdf_for_proforma(db: Session, db_proforma: Proforma) -> Proforma:
    data = {
        "reference": db_proforma.reference,
        "client": db_proforma.client,
        "nombre_personnes": db_proforma.nombre_personnes,
        "objet": db_proforma.objet,
        "date_proforma": db_proforma.date_proforma,
        "sections": db_proforma.sections,
        "frais_agence": db_proforma.frais_agence,
        "details_frais_agence": db_proforma.details_frais_agence,
        "taux_tva_frais_agence": db_proforma.taux_tva_frais_agence,
        "modalite_paiement": db_proforma.modalite_paiement,
        "notes": db_proforma.notes,
    }
    pdf_path = generate_proforma_pdf(data)
    db_proforma.fichier_pdf = _relative_backend_path(pdf_path)
    db_proforma.statut = "pdf_genere"
    db.commit()
    db.refresh(db_proforma)
    return db_proforma


def get_pdf_path(db_proforma: Proforma) -> Path | None:
    return _absolute_backend_path(db_proforma.fichier_pdf)
