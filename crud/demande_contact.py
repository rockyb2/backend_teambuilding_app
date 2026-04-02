from typing import Optional

from sqlalchemy.orm import Session

from database.models import DemandeContact
from database.schemas import DemandeContactCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_demande_contact(db: Session, demande_id: int) -> Optional[DemandeContact]:
    return db.query(DemandeContact).filter(DemandeContact.id == demande_id).first()


def get_demandes_contact(db: Session, skip: int = 0, limit: int = 100) -> list[DemandeContact]:
    return (
        db.query(DemandeContact)
        .order_by(DemandeContact.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_demande_contact(db: Session, payload: DemandeContactCreate) -> DemandeContact:
    db_demande = DemandeContact(**_model_dump(payload))
    db.add(db_demande)
    db.commit()
    db.refresh(db_demande)
    return db_demande
