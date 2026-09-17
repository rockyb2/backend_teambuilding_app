from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from sqlalchemy.orm import Session

from database.models import Budget, DemandeTeamBuilding, DemandeTourisme, DemandeTourismeCustom, OffreTourisme, Proforma
from crud.budget import lock_offer, budget_document_data
from database.schemas import ProformaCreate, ProformaUpdate
from services.proforma_pdf import (
    BASE_DIR,
    TEAMBUILDING_AGENCY_FEE_RATE,
    calculate_totals,
    generate_proforma_pdf,
    is_proforma_pdf_current,
)
from services.proforma_word import generate_proforma_word, get_proforma_word_path, is_proforma_word_current
from services.agency_fees import resolve_agency_fee_rate


PROFORMA_REFERENCE_PREFIX = "PRO"
TOURISM_AGENCY_FEE_RATE = Decimal("0.20")


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
    sections = values.get("sections") or []
    vat_rate = values.get("taux_tva_frais_agence")
    if vat_rate is None:
        vat_rate = 18
    agency_fees = values.get("frais_agence") or 0
    agency_fee_rate = None
    if values.get("pole") == "teambuilding" and not values.get("budget_id"):
        agency_fee_rate = TEAMBUILDING_AGENCY_FEE_RATE
    elif values.get("pole") == "tourisme":
        agency_fee_rate = TOURISM_AGENCY_FEE_RATE
    agency_fee_rate = resolve_agency_fee_rate(values.get("mode_frais_agence"), agency_fee_rate)

    totals = calculate_totals(
        sections,
        agency_fees,
        vat_rate,
        agency_fee_rate=agency_fee_rate,
    )
    values["sections"] = totals["sections"]
    values["frais_agence"] = totals["frais_agence"]
    values["taux_tva_frais_agence"] = totals["taux_tva_frais_agence"]
    values["sous_total_ht"] = totals["sous_total_ht"]
    values["tva_frais_agence"] = totals["tva_frais_agence"]
    values["total_ttc"] = totals["total_ttc"]
    values["details_frais_agence"] = values.get("details_frais_agence") or []
    values["client_details"] = (
        values.get("client_details")
        if isinstance(values.get("client_details"), dict)
        else {}
    )
    values["recommandations"] = values.get("recommandations") or []
    return values


def _validated_budget(db: Session, budget_id: int) -> Budget:
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise ValueError("Budget non trouvé.")
    lock_offer(db, budget.offre_id)
    db.refresh(budget)
    if budget.statut != "valide":
        raise ValueError("Seul le budget validé de l'offre peut servir à une nouvelle proforma.")
    return budget


def build_proforma_from_budget(db: Session, budget_id: int) -> dict:
    budget = _validated_budget(db, budget_id)
    demande = db.query(DemandeTeamBuilding).filter(DemandeTeamBuilding.id == budget.demande_team_building_id).first()
    return {
        "pole": "teambuilding", "budget_id": budget.id,
        "demande_team_building_id": budget.demande_team_building_id,
        "offre_id": budget.offre_id, "site_id": budget.site_id,
        "client": budget.client,
        "client_details": {
            key: getattr(demande, attribute, None) or ""
            for key, attribute in {
                "adresse": "adresse", "contact": "nom_contact",
                "telephone": "telephone_contact", "email": "email_contact",
            }.items()
        },
        "nombre_personnes": budget.nombre_personnes,
        "objet": budget.titre, "date_proforma": date.today(), "date_evenement": budget.date_evenement,
        "sections": deepcopy(budget.sections), "frais_agence": budget.frais_agence,
        "mode_frais_agence": budget.mode_frais_agence,
        "taux_tva_frais_agence": budget.taux_tva_frais_agence,
        "details_frais_agence": [], "modalite_paiement": budget.modalite_paiement,
        "notes": budget.notes, "recommandations": [], "statut": "validee",
    }


def _attach_budget(db: Session, values: dict, existing: Proforma | None = None) -> dict:
    budget_id = values.get("budget_id")
    if values.get("pole") != "teambuilding":
        if budget_id:
            raise ValueError("Les budgets team building ne peuvent pas être utilisés pour le tourisme.")
        return values
    if existing and budget_id == existing.budget_id:
        # An existing proforma keeps its snapshot, even after another budget is chosen.
        if budget_id and any(values.get(key) != getattr(existing, key) for key in ("offre_id", "site_id", "demande_team_building_id")):
            raise ValueError("Le contexte doit correspondre au budget de la proforma.")
        values["budget_snapshot"] = deepcopy(existing.budget_snapshot)
        return values
    if not budget_id:
        raise ValueError("Sélectionnez le budget validé de l'offre pour créer la proforma.")
    budget = _validated_budget(db, budget_id)
    if values.get("mode_frais_agence") is None:
        values["mode_frais_agence"] = budget.mode_frais_agence
    for key in ("offre_id", "site_id", "demande_team_building_id"):
        if values.get(key) is not None and values[key] != getattr(budget, key):
            raise ValueError("Le budget sélectionné ne correspond pas à l'offre, au site ou à la demande.")
        values[key] = getattr(budget, key)
    values["budget_snapshot"] = jsonable_encoder({
        **budget_document_data(budget), "id": budget.id,
        "updated_at": budget.updated_at, "total_ttc": budget.total_ttc,
    })
    return values


def create_proforma(
    db: Session,
    payload: ProformaCreate,
    created_by_id: int | None = None,
) -> Proforma:
    values = _prepare_values(_attach_budget(db, _model_dump(payload)))
    values["reference"] = generate_proforma_reference(db)
    values["created_by_id"] = created_by_id

    db_proforma = Proforma(**values)
    db.add(db_proforma)
    db.commit()
    db.refresh(db_proforma)
    return db_proforma




# tourisme-specific helpers
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
    if isinstance(demande, DemandeTourismeCustom):
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
    values = _attach_budget(db, values, db_proforma)
    values = _prepare_values(values)
    for key, value in values.items():
        if hasattr(db_proforma, key):
            setattr(db_proforma, key, value)

    db_proforma.fichier_pdf = None
    if db_proforma.reference:
        word_path = get_proforma_word_path(db_proforma.reference)
        if word_path.exists():
            try:
                word_path.unlink()
            except OSError:
                pass

    db.commit()
    db.refresh(db_proforma)
    return db_proforma


def _document_data(db_proforma: Proforma) -> dict:
    return {
        "budget_id": db_proforma.budget_id,
        "pole": db_proforma.pole,
        "reference": db_proforma.reference,
        "client": db_proforma.client,
        "client_details": db_proforma.client_details,
        "nombre_personnes": db_proforma.nombre_personnes,
        "objet": db_proforma.objet,
        "date_proforma": db_proforma.date_proforma,
        "date_evenement": db_proforma.date_evenement,
        "sections": db_proforma.sections,
        "frais_agence": db_proforma.frais_agence,
        "mode_frais_agence": db_proforma.mode_frais_agence,
        "details_frais_agence": db_proforma.details_frais_agence,
        "taux_tva_frais_agence": db_proforma.taux_tva_frais_agence,
        "modalite_paiement": db_proforma.modalite_paiement,
        "notes": db_proforma.notes,
    }


def generate_pdf_for_proforma(db: Session, db_proforma: Proforma) -> Proforma:
    data = _document_data(db_proforma)
    pdf_path = generate_proforma_pdf(data)
    db_proforma.fichier_pdf = _relative_backend_path(pdf_path)
    db_proforma.statut = "pdf_genere"
    db.commit()
    db.refresh(db_proforma)
    return db_proforma


def generate_word_for_proforma(db_proforma: Proforma) -> Path:
    return Path(generate_proforma_word(_document_data(db_proforma)))


def get_download_filename(db_proforma: Proforma, extension: str) -> str:
    base_name = str(db_proforma.objet or db_proforma.reference or "proforma").strip()
    clean_name = "".join(
        char if char.isalnum() or char in (" ", "-", "_") else " "
        for char in base_name
    )
    clean_name = " ".join(clean_name.split()) or str(db_proforma.reference or "proforma")
    clean_extension = extension.lstrip(".")
    return f"{clean_name}.{clean_extension}"


def get_pdf_path(db_proforma: Proforma) -> Path | None:
    path = _absolute_backend_path(db_proforma.fichier_pdf)
    return path if path and is_proforma_pdf_current(path) else None


def get_word_path(db_proforma: Proforma) -> Path | None:
    if not db_proforma.reference:
        return None
    path = get_proforma_word_path(db_proforma.reference)
    return path if is_proforma_word_current(path) else None
