from typing import Optional
from sqlalchemy.orm import Session

from database.models import Jeu
from database.schemas import JeuCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_jeu(db: Session, jeu_id: int) -> Optional[Jeu]:
    return db.query(Jeu).filter(Jeu.id_jeu == jeu_id).first()


def get_jeus(db: Session, skip: int = 0, limit: int = 100) -> list[Jeu]:
    return db.query(Jeu).offset(skip).limit(limit).all()


def create_jeu(db: Session, payload: JeuCreate) -> Jeu:
    db_jeu = Jeu(**_model_dump(payload))
    db.add(db_jeu)
    db.commit()
    db.refresh(db_jeu)
    return db_jeu


def update_jeu(db: Session, db_jeu: Jeu, payload: dict) -> Jeu:
    updates = {k: v for k, v in payload.items() if v is not None}
    for key, value in updates.items():
        setattr(db_jeu, key, value)
    db.commit()
    db.refresh(db_jeu)
    return db_jeu


def delete_jeu(db: Session, db_jeu: Jeu) -> None:
    db.delete(db_jeu)
    db.commit()
