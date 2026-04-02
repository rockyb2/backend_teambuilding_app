from typing import Optional

from sqlalchemy.orm import Session

from database.models import DemandeTourisme
from database.schemas import DemandeTourismeCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_demande_tourisme(db: Session, demande_id: int) -> Optional[DemandeTourisme]:
    return db.query(DemandeTourisme).filter(DemandeTourisme.id == demande_id).first()


def get_demandes_tourisme(db: Session, skip: int = 0, limit: int = 100) -> list[DemandeTourisme]:
    return (
        db.query(DemandeTourisme)
        .order_by(DemandeTourisme.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_demande_tourisme(db: Session, payload: DemandeTourismeCreate) -> DemandeTourisme:
    db_demande = DemandeTourisme(**_model_dump(payload))
    db.add(db_demande)
    db.commit()
    db.refresh(db_demande)
    return db_demande
