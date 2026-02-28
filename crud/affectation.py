from typing import Optional
from sqlalchemy.orm import Session

from database.models import Affectation
from database.schemas import AffectationCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_affectation(db: Session, affectation_id: int) -> Optional[Affectation]:
    return db.query(Affectation).filter(Affectation.id_affectation == affectation_id).first()


def get_affectations(db: Session, skip: int = 0, limit: int = 100) -> list[Affectation]:
    return db.query(Affectation).offset(skip).limit(limit).all()


def get_affectations_by_activite(db: Session, activite_id: int) -> list[Affectation]:
    return db.query(Affectation).filter(Affectation.id_activite == activite_id).all()


def get_affectations_by_personnel(db: Session, personnel_id: int, skip: int = 0, limit: int = 100) -> list[Affectation]:
    return db.query(Affectation).filter(Affectation.id_personnel == personnel_id).offset(skip).limit(limit).all()


def create_affectation(db: Session, payload: AffectationCreate) -> Affectation:
    db_affectation = Affectation(**_model_dump(payload))
    db.add(db_affectation)
    db.commit()
    db.refresh(db_affectation)
    return db_affectation


def update_affectation(db: Session, db_affectation: Affectation, payload: dict) -> Affectation:
    updates = {k: v for k, v in payload.items() if v is not None}
    for key, value in updates.items():
        setattr(db_affectation, key, value)
    db.commit()
    db.refresh(db_affectation)
    return db_affectation


def delete_affectation(db: Session, db_affectation: Affectation) -> None:
    db.delete(db_affectation)
    db.commit()
