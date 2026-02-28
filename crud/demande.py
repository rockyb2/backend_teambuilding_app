from typing import Optional
from sqlalchemy.orm import Session

from database.models import Demande
from database.schemas import DemandeCreate, DemandeRead


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_demande(db: Session, demande_id: int) -> Optional[Demande]:
    return db.query(Demande).filter(Demande.id_demande == demande_id).first()


def get_demandes(db: Session, skip: int = 0, limit: int = 100) -> list[Demande]:
    return db.query(Demande).offset(skip).limit(limit).all()


def get_demandes_by_client(db: Session, client_id: int, skip: int = 0, limit: int = 100) -> list[Demande]:
    return db.query(Demande).filter(Demande.id_client == client_id).offset(skip).limit(limit).all()


def get_demandes_by_utilisateur(db: Session, utilisateur_id: int, skip: int = 0, limit: int = 100) -> list[Demande]:
    return db.query(Demande).filter(Demande.id_utilisateur == utilisateur_id).offset(skip).limit(limit).all()


def create_demande(db: Session, payload: DemandeCreate) -> Demande:
    db_demande = Demande(**_model_dump(payload))
    db.add(db_demande)
    db.commit()
    db.refresh(db_demande)
    return db_demande


def update_demande(db: Session, db_demande: Demande, payload: dict) -> Demande:
    updates = {k: v for k, v in payload.items() if v is not None}
    for key, value in updates.items():
        setattr(db_demande, key, value)
    db.commit()
    db.refresh(db_demande)
    return db_demande


def delete_demande(db: Session, db_demande: Demande) -> None:
    db.delete(db_demande)
    db.commit()
