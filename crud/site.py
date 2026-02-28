from typing import Optional
from sqlalchemy.orm import Session

from database.models import Site
from database.schemas import SiteCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_site(db: Session, site_id: int) -> Optional[Site]:
    return db.query(Site).filter(Site.id_site == site_id).first()


def get_sites(db: Session, skip: int = 0, limit: int = 100) -> list[Site]:
    return db.query(Site).offset(skip).limit(limit).all()


def create_site(db: Session, payload: SiteCreate) -> Site:
    db_site = Site(**_model_dump(payload))
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return db_site


def update_site(db: Session, db_site: Site, payload: dict) -> Site:
    updates = {k: v for k, v in payload.items() if v is not None}
    for key, value in updates.items():
        setattr(db_site, key, value)
    db.commit()
    db.refresh(db_site)
    return db_site


def delete_site(db: Session, db_site: Site) -> None:
    db.delete(db_site)
    db.commit()
