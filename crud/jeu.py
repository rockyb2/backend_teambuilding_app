from typing import Optional
from sqlalchemy.orm import Session

from database.models import Jeu
from database.schemas import JeuCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def _normalize_jeu_data(data: dict) -> dict:
    normalized = dict(data)
    if "nb_participant_max" in normalized and "nb_max_participants" not in normalized:
        normalized["nb_max_participants"] = normalized["nb_participant_max"]
    if "nb_max_participants" in normalized and "nb_participant_max" not in normalized:
        normalized["nb_participant_max"] = normalized["nb_max_participants"]
    return normalized


def get_jeu(db: Session, jeu_id: int) -> Optional[Jeu]:
    return db.query(Jeu).filter(Jeu.id_jeu == jeu_id).first()


def get_jeus(db: Session, skip: int = 0, limit: int = 100) -> list[Jeu]:
    return db.query(Jeu).offset(skip).limit(limit).all()


def create_jeu(db: Session, payload: JeuCreate) -> Jeu:
    db_jeu = Jeu(**_normalize_jeu_data(_model_dump(payload)))
    db.add(db_jeu)
    db.commit()
    db.refresh(db_jeu)
    return db_jeu


def update_jeu(db: Session, db_jeu: Jeu, payload: dict) -> Jeu:
    updates = _normalize_jeu_data(payload)
    for key, value in updates.items():
        if hasattr(db_jeu, key):
            setattr(db_jeu, key, value)
    db.commit()
    db.refresh(db_jeu)
    return db_jeu


def delete_jeu(db: Session, db_jeu: Jeu) -> None:
    db.delete(db_jeu)
    db.commit()
