from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.models import Activite
from database.schemas import ActiviteCreate, ActiviteUpdate

ACTIVITE_REFERENCE_PREFIX = "ACT"


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_activite(db: Session, activite_id: int) -> Optional[Activite]:
    return db.query(Activite).filter(Activite.id == activite_id).first()


def get_activite_by_reference(db: Session, reference: str) -> Optional[Activite]:
    return db.query(Activite).filter(Activite.reference == reference).first()


def generate_activite_reference(db: Session, created_at: datetime | None = None) -> str:
    reference_date = created_at or datetime.now()
    month_key = reference_date.strftime("%Y%m")
    prefix = f"{ACTIVITE_REFERENCE_PREFIX}-{month_key}-"

    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"activite-reference-{month_key}"},
        )

    references = db.query(Activite.reference).filter(Activite.reference.like(f"{prefix}%")).all()
    highest_rank = 0
    for (reference,) in references:
        suffix = reference.removeprefix(prefix) if reference else ""
        if suffix.isdigit():
            highest_rank = max(highest_rank, int(suffix))

    return f"{prefix}{highest_rank + 1:03d}"


def get_activites(db: Session, skip: int = 0, limit: int = 100) -> list[Activite]:
    return db.query(Activite).order_by(Activite.created_at.desc()).offset(skip).limit(limit).all()


def get_activite_by_offre(db: Session, offre_id: int) -> Optional[Activite]:
    return db.query(Activite).filter(Activite.offre_id == offre_id).first()


def get_activites_by_demande(db: Session, demande_id: int, skip: int = 0, limit: int = 100) -> list[Activite]:
    return (
        db.query(Activite)
        .filter(Activite.demande_id == demande_id)
        .order_by(Activite.date_debut.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_activites_by_client(db: Session, client_id: int, skip: int = 0, limit: int = 100) -> list[Activite]:
    return (
        db.query(Activite)
        .filter(Activite.client_id == client_id)
        .order_by(Activite.date_debut.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_activites_by_site(db: Session, site_id: int, skip: int = 0, limit: int = 100) -> list[Activite]:
    return (
        db.query(Activite)
        .filter(Activite.site_id == site_id)
        .order_by(Activite.date_debut.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_activites_by_responsable(db: Session, responsable_id: int, skip: int = 0, limit: int = 100) -> list[Activite]:
    return (
        db.query(Activite)
        .filter(Activite.responsable_id == responsable_id)
        .order_by(Activite.date_debut.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_activite(db: Session, payload: ActiviteCreate) -> Activite:
    values = _model_dump(payload)
    values.pop("reference", None)
    values["reference"] = generate_activite_reference(db)
    db_activite = Activite(**values)
    db.add(db_activite)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_activite)
    return db_activite


def update_activite(db: Session, db_activite: Activite, payload: ActiviteUpdate | dict) -> Activite:
    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    for key, value in updates.items():
        if hasattr(db_activite, key):
            setattr(db_activite, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_activite)
    return db_activite


def delete_activite(db: Session, db_activite: Activite) -> None:
    db.delete(db_activite)
    db.commit()
