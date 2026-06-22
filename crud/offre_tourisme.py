from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from database.models import (
    DemandeTourisme,
    DemandeTourismeCustom,
    HistoriqueStatutDemandeTourisme,
    OffreTourisme,
)
from database.schemas import OffreTourismeCreate, OffreTourismeUpdate

OFFRE_TOURISME_REFERENCE_PREFIX = "OFF-TOUR"


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_offre_tourisme(db: Session, offre_id: int) -> Optional[OffreTourisme]:
    return db.query(OffreTourisme).filter(OffreTourisme.id == offre_id).first()


def get_offres_tourisme(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[OffreTourisme]:
    return (
        db.query(OffreTourisme)
        .order_by(OffreTourisme.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def generate_offre_tourisme_reference(
    db: Session,
    created_at: datetime | None = None,
) -> str:
    reference_date = created_at or datetime.now()
    month_key = reference_date.strftime("%Y%m")
    prefix = f"{OFFRE_TOURISME_REFERENCE_PREFIX}-{month_key}-"

    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"offre-tourisme-reference-{month_key}"},
        )

    references = (
        db.query(OffreTourisme.reference)
        .filter(OffreTourisme.reference.like(f"{prefix}%"))
        .all()
    )
    highest_rank = 0
    for (reference,) in references:
        suffix = reference.removeprefix(prefix) if reference else ""
        if suffix.isdigit():
            highest_rank = max(highest_rank, int(suffix))

    return f"{prefix}{highest_rank + 1:03d}"


def _sync_demande_status_from_offres(
    db: Session,
    demande_tourisme_id: int | None = None,
    demande_tourisme_custom_id: int | None = None,
    utilisateur_id: int | None = None,
) -> None:
    if demande_tourisme_id is not None:
        demande = (
            db.query(DemandeTourisme)
            .filter(DemandeTourisme.id == demande_tourisme_id)
            .first()
        )
        offer_filter = OffreTourisme.demande_tourisme_id == demande_tourisme_id
    elif demande_tourisme_custom_id is not None:
        demande = (
            db.query(DemandeTourismeCustom)
            .filter(DemandeTourismeCustom.id == demande_tourisme_custom_id)
            .first()
        )
        offer_filter = (
            OffreTourisme.demande_tourisme_custom_id
            == demande_tourisme_custom_id
        )
    else:
        return

    if not demande or demande.statut in {"annulee", "terminee"}:
        return

    offer_statuses = {
        statut
        for (statut,) in (
            db.query(OffreTourisme.statut)
            .filter(offer_filter)
            .all()
        )
    }

    target_status = (
        "validee"
        if "validee" in offer_statuses
        else "devis_envoye"
        if "envoyee" in offer_statuses
        else "refusee"
        if "refusee" in offer_statuses
        else "contactee"
        if demande.statut != "nouvelle"
        else None
    )
    if not target_status or demande.statut == target_status:
        return

    ancien_statut = demande.statut
    modifie_le = datetime.utcnow()
    demande.statut = target_status
    demande.statut_modifie_le = modifie_le
    demande.statut_modifie_par_id = utilisateur_id
    if isinstance(demande, DemandeTourismeCustom):
        demande.updated_by_id = utilisateur_id
        demande.updated_at = modifie_le

    db.add(
        HistoriqueStatutDemandeTourisme(
            demande_tourisme_id=demande_tourisme_id,
            demande_tourisme_custom_id=demande_tourisme_custom_id,
            ancien_statut=ancien_statut,
            nouveau_statut=target_status,
            commentaire="Statut synchronise depuis une offre tourisme",
            modifie_par_id=utilisateur_id,
            modifie_le=modifie_le,
        )
    )


def create_offre_tourisme(
    db: Session,
    payload: OffreTourismeCreate,
    created_by_id: int | None = None,
) -> OffreTourisme:
    values = _model_dump(payload)
    values["reference"] = generate_offre_tourisme_reference(db)
    values["created_by_id"] = created_by_id
    db_offre = OffreTourisme(**values)
    db.add(db_offre)
    db.flush()
    _sync_demande_status_from_offres(
        db,
        demande_tourisme_id=db_offre.demande_tourisme_id,
        demande_tourisme_custom_id=db_offre.demande_tourisme_custom_id,
        utilisateur_id=created_by_id,
    )
    db.commit()
    db.refresh(db_offre)
    return db_offre


def update_offre_tourisme(
    db: Session,
    db_offre: OffreTourisme,
    payload: OffreTourismeUpdate | dict,
    updated_by_id: int | None = None,
) -> OffreTourisme:
    previous_target = (
        db_offre.demande_tourisme_id,
        db_offre.demande_tourisme_custom_id,
    )
    updates = (
        _model_dump(payload, exclude_unset=True)
        if not isinstance(payload, dict)
        else dict(payload)
    )
    for key, value in updates.items():
        if hasattr(db_offre, key):
            setattr(db_offre, key, value)

    db.flush()
    current_target = (
        db_offre.demande_tourisme_id,
        db_offre.demande_tourisme_custom_id,
    )
    for demande_tourisme_id, demande_tourisme_custom_id in {
        previous_target,
        current_target,
    }:
        _sync_demande_status_from_offres(
            db,
            demande_tourisme_id=demande_tourisme_id,
            demande_tourisme_custom_id=demande_tourisme_custom_id,
            utilisateur_id=updated_by_id,
        )

    db.commit()
    db.refresh(db_offre)
    return db_offre


def delete_offre_tourisme(
    db: Session,
    db_offre: OffreTourisme,
    utilisateur_id: int | None = None,
) -> None:
    target = (
        db_offre.demande_tourisme_id,
        db_offre.demande_tourisme_custom_id,
    )
    db.delete(db_offre)
    db.flush()
    _sync_demande_status_from_offres(
        db,
        demande_tourisme_id=target[0],
        demande_tourisme_custom_id=target[1],
        utilisateur_id=utilisateur_id,
    )
    db.commit()
