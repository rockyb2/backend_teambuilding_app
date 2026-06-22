from typing import Optional

from sqlalchemy.orm import Session

from database.models import Materiel
from database.schemas import MaterielCreate, MaterielUpdate


def _model_dump(schema_obj, **kwargs):
    if isinstance(schema_obj, dict):
        return dict(schema_obj)
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_materiel(db: Session, materiel_id: int) -> Optional[Materiel]:
    return db.query(Materiel).filter(Materiel.id == materiel_id).first()


def get_materiel_by_nom(db: Session, nom: str) -> Optional[Materiel]:
    return db.query(Materiel).filter(Materiel.nom == nom).first()


def get_materiels(db: Session, skip: int = 0, limit: int = 100) -> list[Materiel]:
    return db.query(Materiel).order_by(Materiel.nom.asc()).offset(skip).limit(limit).all()


def create_materiel(db: Session, payload: MaterielCreate) -> Materiel:
    db_materiel = Materiel(**_model_dump(payload))
    db.add(db_materiel)
    db.commit()
    db.refresh(db_materiel)
    return db_materiel


def update_materiel(db: Session, db_materiel: Materiel, payload: MaterielUpdate | dict) -> Materiel:
    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    for key, value in updates.items():
        if hasattr(db_materiel, key):
            setattr(db_materiel, key, value)
    db.commit()
    db.refresh(db_materiel)
    return db_materiel


def delete_materiel(db: Session, db_materiel: Materiel) -> None:
    db.delete(db_materiel)
    db.commit()
