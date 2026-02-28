from typing import Optional
from sqlalchemy.orm import Session

from database.models import Activite
from database.schemas import ActiviteCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_activite(db: Session, activite_id: int) -> Optional[Activite]:
    return db.query(Activite).filter(Activite.id_activite == activite_id).first()


def get_activites(db: Session, skip: int = 0, limit: int = 100) -> list[Activite]:
    return db.query(Activite).offset(skip).limit(limit).all()


def get_activites_by_offre(db: Session, offre_id: int) -> Optional[Activite]:
    return db.query(Activite).filter(Activite.id_offre == offre_id).first()


def get_activites_by_site(db: Session, site_id: int, skip: int = 0, limit: int = 100) -> list[Activite]:
    return db.query(Activite).filter(Activite.id_site == site_id).offset(skip).limit(limit).all()


def create_activite(db: Session, payload: ActiviteCreate) -> Activite:
    db_activite = Activite(**_model_dump(payload))
    db.add(db_activite)
    db.commit()
    db.refresh(db_activite)
    return db_activite


def update_activite(db: Session, db_activite: Activite, payload: dict) -> Activite:
    updates = {k: v for k, v in payload.items() if v is not None}
    for key, value in updates.items():
        setattr(db_activite, key, value)
    db.commit()
    db.refresh(db_activite)
    return db_activite


def delete_activite(db: Session, db_activite: Activite) -> None:
    db.delete(db_activite)
    db.commit()
