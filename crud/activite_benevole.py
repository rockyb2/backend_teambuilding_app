from typing import Optional

from sqlalchemy.orm import Session

from database.models import ActiviteBenevole
from database.schemas import ActiviteBenevoleCreate, ActiviteBenevoleUpdate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_activite_benevole(db: Session, activite_benevole_id: int) -> Optional[ActiviteBenevole]:
    return db.query(ActiviteBenevole).filter(ActiviteBenevole.id == activite_benevole_id).first()


def get_activite_benevole_by_pair(db: Session, activite_id: int, benevole_id: int) -> Optional[ActiviteBenevole]:
    return (
        db.query(ActiviteBenevole)
        .filter(
            ActiviteBenevole.activite_id == activite_id,
            ActiviteBenevole.benevole_id == benevole_id,
        )
        .first()
    )


def get_activites_benevoles(db: Session, skip: int = 0, limit: int = 100) -> list[ActiviteBenevole]:
    return db.query(ActiviteBenevole).offset(skip).limit(limit).all()


def get_benevoles_by_activite(db: Session, activite_id: int) -> list[ActiviteBenevole]:
    return db.query(ActiviteBenevole).filter(ActiviteBenevole.activite_id == activite_id).all()


def get_activites_by_benevole(db: Session, benevole_id: int, skip: int = 0, limit: int = 100) -> list[ActiviteBenevole]:
    return (
        db.query(ActiviteBenevole)
        .filter(ActiviteBenevole.benevole_id == benevole_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_activite_benevole(db: Session, payload: ActiviteBenevoleCreate) -> ActiviteBenevole:
    db_activite_benevole = ActiviteBenevole(**_model_dump(payload))
    db.add(db_activite_benevole)
    db.commit()
    db.refresh(db_activite_benevole)
    return db_activite_benevole


def update_activite_benevole(
    db: Session,
    db_activite_benevole: ActiviteBenevole,
    payload: ActiviteBenevoleUpdate | dict,
) -> ActiviteBenevole:
    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    for key, value in updates.items():
        if hasattr(db_activite_benevole, key):
            setattr(db_activite_benevole, key, value)
    db.commit()
    db.refresh(db_activite_benevole)
    return db_activite_benevole


def delete_activite_benevole(db: Session, db_activite_benevole: ActiviteBenevole) -> None:
    db.delete(db_activite_benevole)
    db.commit()
