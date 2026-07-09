from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from database.models import CategorieDepense, Depense
from database.schemas import (
    CategorieDepenseCreate,
    CategorieDepenseUpdate,
    DepenseCreate,
    DepenseUpdate,
)

DEPENSE_REFERENCE_PREFIX = "DEP"


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_categorie_depense(db: Session, categorie_id: int) -> Optional[CategorieDepense]:
    return db.query(CategorieDepense).filter(CategorieDepense.id == categorie_id).first()


def get_categorie_depense_by_nom(db: Session, nom: str) -> Optional[CategorieDepense]:
    return db.query(CategorieDepense).filter(CategorieDepense.nom == nom).first()


def get_categories_depenses(db: Session, skip: int = 0, limit: int = 100) -> list[CategorieDepense]:
    return db.query(CategorieDepense).order_by(CategorieDepense.nom.asc()).offset(skip).limit(limit).all()


def create_categorie_depense(db: Session, payload: CategorieDepenseCreate) -> CategorieDepense:
    db_categorie = CategorieDepense(**_model_dump(payload))
    db.add(db_categorie)
    db.commit()
    db.refresh(db_categorie)
    return db_categorie


def update_categorie_depense(
    db: Session,
    db_categorie: CategorieDepense,
    payload: CategorieDepenseUpdate | dict,
) -> CategorieDepense:
    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    for key, value in updates.items():
        if hasattr(db_categorie, key):
            setattr(db_categorie, key, value)
    db.commit()
    db.refresh(db_categorie)
    return db_categorie


def delete_categorie_depense(db: Session, db_categorie: CategorieDepense) -> None:
    db.delete(db_categorie)
    db.commit()


def get_depense(db: Session, depense_id: int) -> Optional[Depense]:
    return db.query(Depense).filter(Depense.id == depense_id).first()


def get_depense_by_reference(db: Session, reference: str) -> Optional[Depense]:
    return db.query(Depense).filter(Depense.reference == reference).first()


def generate_depense_reference(db: Session, created_at: datetime | None = None) -> str:
    reference_date = created_at or datetime.now()
    month_key = reference_date.strftime("%Y%m")
    prefix = f"{DEPENSE_REFERENCE_PREFIX}-{month_key}-"

    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"depense-reference-{month_key}"},
        )

    references = db.query(Depense.reference).filter(Depense.reference.like(f"{prefix}%")).all()
    highest_rank = 0
    for (reference,) in references:
        suffix = reference.removeprefix(prefix) if reference else ""
        if suffix.isdigit():
            highest_rank = max(highest_rank, int(suffix))

    return f"{prefix}{highest_rank + 1:03d}"


def get_depenses(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    pole: str | None = None,
    facture_id: int | None = None,
    proforma_id: int | None = None,
    demande_team_building_id: int | None = None,
    demande_tourisme_id: int | None = None,
    demande_tourisme_custom_id: int | None = None,
) -> list[Depense]:
    query = db.query(Depense)
    if pole:
        query = query.filter(Depense.pole == pole)
    if facture_id is not None:
        query = query.filter(Depense.facture_id == facture_id)
    if proforma_id is not None:
        query = query.filter(Depense.proforma_id == proforma_id)
    if demande_team_building_id is not None:
        query = query.filter(Depense.demande_team_building_id == demande_team_building_id)
    if demande_tourisme_id is not None:
        query = query.filter(Depense.demande_tourisme_id == demande_tourisme_id)
    if demande_tourisme_custom_id is not None:
        query = query.filter(Depense.demande_tourisme_custom_id == demande_tourisme_custom_id)
    return query.order_by(Depense.date_depense.desc().nulls_last()).offset(skip).limit(limit).all()


def get_depenses_by_activite(db: Session, activite_id: int, skip: int = 0, limit: int = 100) -> list[Depense]:
    return (
        db.query(Depense)
        .filter(Depense.activite_id == activite_id)
        .order_by(Depense.date_depense.desc().nulls_last())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_depenses_by_offre(db: Session, offre_id: int, skip: int = 0, limit: int = 100) -> list[Depense]:
    return (
        db.query(Depense)
        .filter(Depense.offre_id == offre_id)
        .order_by(Depense.date_depense.desc().nulls_last())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_depenses_by_categorie(db: Session, categorie_id: int, skip: int = 0, limit: int = 100) -> list[Depense]:
    return (
        db.query(Depense)
        .filter(Depense.categorie_depense_id == categorie_id)
        .order_by(Depense.date_depense.desc().nulls_last())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_depense(db: Session, payload: DepenseCreate) -> Depense:
    values = _model_dump(payload)
    values.pop("reference", None)
    values["pole"] = values.get("pole") or "teambuilding"
    values["reference"] = generate_depense_reference(db)
    db_depense = Depense(**values)
    db.add(db_depense)
    db.commit()
    db.refresh(db_depense)
    return db_depense


def update_depense(db: Session, db_depense: Depense, payload: DepenseUpdate | dict) -> Depense:
    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    for key, value in updates.items():
        if hasattr(db_depense, key):
            setattr(db_depense, key, value)
    db.commit()
    db.refresh(db_depense)
    return db_depense


def delete_depense(db: Session, db_depense: Depense) -> None:
    db.delete(db_depense)
    db.commit()
