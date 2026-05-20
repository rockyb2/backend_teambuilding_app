from typing import Optional
from sqlalchemy.orm import Session, selectinload

from database.models import Site, SiteImage
from database.schemas import SiteCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_site(db: Session, site_id: int) -> Optional[Site]:
    return db.query(Site).options(selectinload(Site.images)).filter(Site.id_site == site_id).first()


def get_sites(db: Session, skip: int = 0, limit: int = 100) -> list[Site]:
    return db.query(Site).options(selectinload(Site.images)).offset(skip).limit(limit).all()


def _normalize_site_images(images) -> list[dict]:
    normalized_images = []
    for index, image in enumerate(images or []):
        if isinstance(image, str):
            image_url = image.strip()
            if image_url:
                normalized_images.append({"image_url": image_url, "alt": None, "ordre": index})
            continue

        image_url_raw = image.get("image_url") if isinstance(image, dict) else getattr(image, "image_url", "")
        image_url = str(image_url_raw or "").strip()
        if not image_url:
            continue
        alt = image.get("alt") if isinstance(image, dict) else getattr(image, "alt", None)
        ordre = image.get("ordre", index) if isinstance(image, dict) else getattr(image, "ordre", index)
        normalized_images.append({"image_url": image_url, "alt": alt, "ordre": ordre or 0})
    return normalized_images


def _replace_site_images(db_site: Site, images) -> None:
    normalized_images = _normalize_site_images(images)
    db_site.images.clear()
    for image in normalized_images:
        db_site.images.append(SiteImage(**image))

    if normalized_images and not db_site.image_site:
        db_site.image_site = normalized_images[0]["image_url"]


def create_site(db: Session, payload: SiteCreate) -> Site:
    data = _model_dump(payload)
    images = data.pop("images", [])
    db_site = Site(**data)
    _replace_site_images(db_site, images)
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return get_site(db, db_site.id_site) or db_site


def update_site(db: Session, db_site: Site, payload: dict) -> Site:
    updates = dict(payload)
    images = updates.pop("images", None)
    for key, value in updates.items():
        if hasattr(db_site, key):
            setattr(db_site, key, value)
    if images is not None:
        _replace_site_images(db_site, images)
    db.commit()
    db.refresh(db_site)
    return get_site(db, db_site.id_site) or db_site


def delete_site(db: Session, db_site: Site) -> None:
    db.delete(db_site)
    db.commit()
