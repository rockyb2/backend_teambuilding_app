from typing import Optional

from sqlalchemy.orm import Session

from database.models import Benevole
from database.schemas import BenevoleCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def normalize_benevole_email(email: str | None) -> str | None:
    normalized = (email or "").strip().lower()
    return normalized or None


def get_benevole(db: Session, benevole_id: int) -> Optional[Benevole]:
    return db.query(Benevole).filter(Benevole.id == benevole_id).first()


def get_benevole_by_email(db: Session, email: str) -> Optional[Benevole]:
    normalized_email = normalize_benevole_email(email)
    if not normalized_email:
        return None
    return db.query(Benevole).filter(Benevole.email == normalized_email).first()


def get_benevoles(db: Session, skip: int = 0, limit: int = 100) -> list[Benevole]:
    return db.query(Benevole).order_by(Benevole.created_at.desc()).offset(skip).limit(limit).all()


def create_benevole(db: Session, payload: BenevoleCreate) -> Benevole:
    data = _model_dump(payload)
    data["email"] = normalize_benevole_email(data.get("email"))
    db_benevole = Benevole(**data)
    db.add(db_benevole)
    db.commit()
    db.refresh(db_benevole)
    return db_benevole


def update_benevole(db: Session, db_benevole: Benevole, payload: dict) -> Benevole:
    updates = dict(payload)
    if "email" in updates:
        updates["email"] = normalize_benevole_email(updates["email"])
    for key, value in updates.items():
        setattr(db_benevole, key, value)
    db.commit()
    db.refresh(db_benevole)
    return db_benevole


def delete_benevole(db: Session, db_benevole: Benevole) -> None:
    db.delete(db_benevole)
    db.commit()
