from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from database.models import DemandeTeamBuilding, Offre
from database.schemas import OffreCreate, OffreUpdate

OFFRE_REFERENCE_PREFIX = "OFF"
OFFRE_STATUSES_ELIGIBLES_ACTIVITE = ("validee",)
DEMANDE_STATUS_BY_OFFRE_STATUS = {
    "envoyee": "devis_envoye",
    "validee": "confirmee",
}
OFFRE_STATUSES_TERMINAUX = {"annulee", "refusee", "expiree"}


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_offre(db: Session, offre_id: int) -> Optional[Offre]:
    return db.query(Offre).filter(Offre.id == offre_id).first()


def get_offres(db: Session, skip: int = 0, limit: int = 100) -> list[Offre]:
    return db.query(Offre).order_by(Offre.created_at.desc()).offset(skip).limit(limit).all()


def get_offres_by_demande(db: Session, demande_id: int, skip: int = 0, limit: int = 100) -> list[Offre]:
    return (
        db.query(Offre)
        .filter(Offre.demande_id == demande_id)
        .order_by(Offre.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_offre_by_reference(db: Session, reference: str) -> Optional[Offre]:
    return db.query(Offre).filter(Offre.reference == reference).first()


def generate_offre_reference(db: Session, created_at: datetime | None = None) -> str:
    reference_date = created_at or datetime.now()
    month_key = reference_date.strftime("%Y%m")
    prefix = f"{OFFRE_REFERENCE_PREFIX}-{month_key}-"

    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"offre-reference-{month_key}"},
        )

    references = (
        db.query(Offre.reference)
        .filter(Offre.reference.like(f"{prefix}%"))
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
    demande_id: int,
    utilisateur_id: int | None = None,
) -> None:
    demande = (
        db.query(DemandeTeamBuilding)
        .filter(DemandeTeamBuilding.id == demande_id)
        .first()
    )
    if not demande or demande.statut == "annulee":
        return

    offer_statuses = {
        statut
        for (statut,) in db.query(Offre.statut).filter(Offre.demande_id == demande_id).all()
    }
    target_status = (
        DEMANDE_STATUS_BY_OFFRE_STATUS["validee"]
        if "validee" in offer_statuses
        else DEMANDE_STATUS_BY_OFFRE_STATUS["envoyee"]
        if "envoyee" in offer_statuses
        else "annulee"
        if offer_statuses and offer_statuses <= OFFRE_STATUSES_TERMINAUX
        else None
    )

    if not target_status or demande.statut == target_status:
        return
    if demande.statut == "confirmee" and target_status == "devis_envoye":
        return
    if demande.statut == "confirmee" and target_status == "annulee":
        return

    demande.statut = target_status
    demande.statut_modifie_le = datetime.now(timezone.utc)
    demande.statut_modifie_par_id = utilisateur_id


def create_offre(db: Session, payload: OffreCreate, created_by_id: int | None = None) -> Offre:
    values = _model_dump(payload)
    values.pop("reference", None)
    values["reference"] = generate_offre_reference(db)
    values["id_utilisateur_cr"] = created_by_id

    db_offre = Offre(**values)
    db.add(db_offre)
    db.flush()
    _sync_demande_status_from_offres(db, db_offre.demande_id, created_by_id)
    db.commit()
    db.refresh(db_offre)
    return db_offre


def update_offre(
    db: Session,
    db_offre: Offre,
    payload: OffreUpdate | dict,
    updated_by_id: int | None = None,
) -> Offre:
    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    for key, value in updates.items():
        if hasattr(db_offre, key):
            setattr(db_offre, key, value)
    db.flush()
    _sync_demande_status_from_offres(db, db_offre.demande_id, updated_by_id)
    db.commit()
    db.refresh(db_offre)
    return db_offre


def delete_offre(db: Session, db_offre: Offre) -> None:
    db.delete(db_offre)
    db.commit()
