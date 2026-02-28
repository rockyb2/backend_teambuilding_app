from typing import Optional
from sqlalchemy.orm import Session

from database.models import Depense
from database.schemas import DepenseCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_depense(db: Session, depense_id: int) -> Optional[Depense]:
    return db.query(Depense).filter(Depense.id_depense == depense_id).first()


def get_depenses(db: Session, skip: int = 0, limit: int = 100) -> list[Depense]:
    return db.query(Depense).offset(skip).limit(limit).all()


def get_depenses_by_activite(db: Session, activite_id: int, skip: int = 0, limit: int = 100) -> list[Depense]:
    return db.query(Depense).filter(Depense.id_activite == activite_id).offset(skip).limit(limit).all()


def create_depense(db: Session, payload: DepenseCreate) -> Depense:
    db_depense = Depense(**_model_dump(payload))
    db.add(db_depense)
    db.commit()
    db.refresh(db_depense)
    return db_depense


def update_depense(db: Session, db_depense: Depense, payload: dict) -> Depense:
    updates = {k: v for k, v in payload.items() if v is not None}
    for key, value in updates.items():
        setattr(db_depense, key, value)
    db.commit()
    db.refresh(db_depense)
    return db_depense


def delete_depense(db: Session, db_depense: Depense) -> None:
    db.delete(db_depense)
    db.commit()
