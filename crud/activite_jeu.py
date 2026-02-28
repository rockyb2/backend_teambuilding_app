from typing import Optional
from sqlalchemy.orm import Session

from database.models import ActiviteJeu
from database.schemas import ActiviteJeuCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_activite_jeu(db: Session, activite_id: int, jeu_id: int) -> Optional[ActiviteJeu]:
    return db.query(ActiviteJeu).filter(
        ActiviteJeu.id_activite == activite_id,
        ActiviteJeu.id_jeu == jeu_id
    ).first()


def get_activite_jeux(db: Session, activite_id: int) -> list[ActiviteJeu]:
    return db.query(ActiviteJeu).filter(ActiviteJeu.id_activite == activite_id).all()


def get_jeux_by_activite(db: Session, activite_id: int) -> list[ActiviteJeu]:
    return db.query(ActiviteJeu).filter(ActiviteJeu.id_activite == activite_id).order_by(ActiviteJeu.ordre).all()


def create_activite_jeu(db: Session, payload: ActiviteJeuCreate) -> ActiviteJeu:
    db_activite_jeu = ActiviteJeu(**_model_dump(payload))
    db.add(db_activite_jeu)
    db.commit()
    db.refresh(db_activite_jeu)
    return db_activite_jeu


def update_activite_jeu(db: Session, db_activite_jeu: ActiviteJeu, payload: dict) -> ActiviteJeu:
    updates = {k: v for k, v in payload.items() if v is not None}
    for key, value in updates.items():
        setattr(db_activite_jeu, key, value)
    db.commit()
    db.refresh(db_activite_jeu)
    return db_activite_jeu


def delete_activite_jeu(db: Session, db_activite_jeu: ActiviteJeu) -> None:
    db.delete(db_activite_jeu)
    db.commit()
