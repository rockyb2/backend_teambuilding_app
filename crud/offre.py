from typing import Optional
from sqlalchemy.orm import Session

from database.models import Offre
from database.schemas import OffreCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_offre(db: Session, offre_id: int) -> Optional[Offre]:
    return db.query(Offre).filter(Offre.id_offre == offre_id).first()


def get_offres(db: Session, skip: int = 0, limit: int = 100) -> list[Offre]:
    return db.query(Offre).offset(skip).limit(limit).all()


def get_offres_by_demande(db: Session, demande_id: int, skip: int = 0, limit: int = 100) -> list[Offre]:
    return db.query(Offre).filter(Offre.id_demande == demande_id).offset(skip).limit(limit).all()


def create_offre(db: Session, payload: OffreCreate) -> Offre:
    db_offre = Offre(**_model_dump(payload))
    db.add(db_offre)
    db.commit()
    db.refresh(db_offre)
    return db_offre


def update_offre(db: Session, db_offre: Offre, payload: dict) -> Offre:
    updates = {k: v for k, v in payload.items() if v is not None}
    for key, value in updates.items():
        setattr(db_offre, key, value)
    db.commit()
    db.refresh(db_offre)
    return db_offre


def delete_offre(db: Session, db_offre: Offre) -> None:
    db.delete(db_offre)
    db.commit()
