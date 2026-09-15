from sqlalchemy.orm import Session

from database.event_models import InscriptionEvent
from database.event_schemas import InscriptionEventCreate


def create_inscription(db: Session, payload: InscriptionEventCreate):
    inscription = InscriptionEvent(**payload.model_dump())
    try:
        db.add(inscription)
        db.commit()
        db.refresh(inscription)
    except Exception:
        db.rollback()
        raise
    return inscription