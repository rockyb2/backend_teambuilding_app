from typing import Optional
from sqlalchemy.orm import Session

from database.models import Personnel
from database.schemas import PersonnelCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_personnel(db: Session, personnel_id: int) -> Optional[Personnel]:
    return db.query(Personnel).filter(Personnel.id_personnel == personnel_id).first()


def get_personnel_by_email(db: Session, email: str) -> Optional[Personnel]:
    return db.query(Personnel).filter(Personnel.email == email).first()


def get_personnels(db: Session, skip: int = 0, limit: int = 100) -> list[Personnel]:
    return db.query(Personnel).offset(skip).limit(limit).all()


def get_personnels_disponibles(db: Session, skip: int = 0, limit: int = 100) -> list[Personnel]:
    # La colonne disponibilite a ete supprimee; on conserve l'endpoint pour compatibilite.
    return db.query(Personnel).offset(skip).limit(limit).all()


def create_personnel(db: Session, payload: PersonnelCreate) -> Personnel:
    db_personnel = Personnel(**_model_dump(payload))
    db.add(db_personnel)
    db.commit()
    db.refresh(db_personnel)
    return db_personnel


def update_personnel(db: Session, db_personnel: Personnel, payload: dict) -> Personnel:
    updates = {k: v for k, v in payload.items() if v is not None}
    for key, value in updates.items():
        setattr(db_personnel, key, value)
    db.commit()
    db.refresh(db_personnel)
    return db_personnel


def delete_personnel(db: Session, db_personnel: Personnel) -> None:
    db.delete(db_personnel)
    db.commit()
