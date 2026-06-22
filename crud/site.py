import json
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


def _normalize_site_images(images) -> list[str]:
    normalized_images = []
    for index, image in enumerate(images or []):
        if isinstance(image, str):
            image_url = image.strip()
            if image_url:
                normalized_images.append(image_url)
            continue

        if isinstance(image, dict):
            image_url_raw = image.get("image_url") or image.get("url") or image.get("secure_url") or image.get("src")
        else:
            image_url_raw = getattr(image, "image_url", "") or getattr(image, "url", "")
        image_url = str(image_url_raw or "").strip()
        if not image_url:
            continue
        normalized_images.append(image_url)
    return normalized_images


def _normalize_json_object(value):
    if value in (None, ""):
        return None

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, dict) else None

    return None


def _normalize_site_payload(data: dict, include_empty_images: bool = True) -> dict:
    normalized = dict(data)
    has_legacy_image = "image_site" in normalized
    legacy_image = normalized.pop("image_site", None)
    has_images = "images" in normalized
    images = normalized.get("images")

    if (not images) and legacy_image:
        images = [legacy_image]

    if include_empty_images or has_images or has_legacy_image:
        normalized["images"] = _normalize_site_images(images)
    if "tarifs_restauration" in normalized:
        normalized["tarifs_restauration"] = _normalize_json_object(normalized.get("tarifs_restauration"))
    if "tarifs_seminaire" in normalized:
        normalized["tarifs_seminaire"] = _normalize_json_object(normalized.get("tarifs_seminaire"))
    return normalized


def create_site(db: Session, payload: SiteCreate) -> Site:
    data = _normalize_site_payload(_model_dump(payload))
    db_site = Site(**data)
    db.add(db_site)
    db.commit()
    db.refresh(db_site)
    return get_site(db, db_site.id_site) or db_site


def update_site(db: Session, db_site: Site, payload: dict) -> Site:
    updates = _normalize_site_payload(dict(payload), include_empty_images=False)
    for key, value in updates.items():
        if hasattr(db_site, key):
            setattr(db_site, key, value)
    db.commit()
    db.refresh(db_site)
    return get_site(db, db_site.id_site) or db_site


def delete_site(db: Session, db_site: Site) -> None:
    db.delete(db_site)
    db.commit()
