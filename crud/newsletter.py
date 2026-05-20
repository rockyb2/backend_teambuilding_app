from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.models import NewsletterSubscriber
from database.schemas import NewsletterSubscriptionCreate, NewsletterSubscriptionUpdate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def normalize_newsletter_email(email: str) -> str:
    return (email or "").strip().lower()


def get_newsletter_subscription_by_email(db: Session, email: str) -> Optional[NewsletterSubscriber]:
    normalized_email = normalize_newsletter_email(email)
    return db.query(NewsletterSubscriber).filter(NewsletterSubscriber.email == normalized_email).first()


def get_newsletter_subscription(db: Session, subscription_id: int) -> Optional[NewsletterSubscriber]:
    return db.query(NewsletterSubscriber).filter(NewsletterSubscriber.id == subscription_id).first()


def get_newsletter_subscriptions(db: Session, skip: int = 0, limit: int = 100) -> list[NewsletterSubscriber]:
    return (
        db.query(NewsletterSubscriber)
        .order_by(NewsletterSubscriber.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def _apply_subscription_updates(
    db_subscription: NewsletterSubscriber,
    payload: NewsletterSubscriptionCreate,
) -> NewsletterSubscriber:
    data = _model_dump(payload, exclude_unset=True)
    db_subscription.langue = data.get("langue") or db_subscription.langue
    db_subscription.source = data.get("source") or db_subscription.source or "site_web"
    db_subscription.consentement = bool(data.get("consentement", db_subscription.consentement))
    db_subscription.actif = True
    return db_subscription


def create_or_update_newsletter_subscription(
    db: Session,
    payload: NewsletterSubscriptionCreate,
) -> tuple[NewsletterSubscriber, bool]:
    data = _model_dump(payload, exclude_unset=True)
    normalized_email = normalize_newsletter_email(data.get("email", ""))
    if not normalized_email:
        raise ValueError("Email newsletter manquant")

    existing_subscription = get_newsletter_subscription_by_email(db, normalized_email)
    if existing_subscription:
        _apply_subscription_updates(existing_subscription, payload)
        db.commit()
        db.refresh(existing_subscription)
        return existing_subscription, False

    db_subscription = NewsletterSubscriber(
        email=normalized_email,
        langue=data.get("langue"),
        source=data.get("source") or "site_web",
        consentement=bool(data.get("consentement", True)),
        actif=True,
    )
    db.add(db_subscription)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing_subscription = get_newsletter_subscription_by_email(db, normalized_email)
        if not existing_subscription:
            raise
        _apply_subscription_updates(existing_subscription, payload)
        db.commit()
        db.refresh(existing_subscription)
        return existing_subscription, False

    db.refresh(db_subscription)
    return db_subscription, True


def create_newsletter_subscription(
    db: Session,
    payload: NewsletterSubscriptionCreate,
) -> NewsletterSubscriber:
    data = _model_dump(payload, exclude_unset=True)
    normalized_email = normalize_newsletter_email(data.get("email", ""))
    if not normalized_email:
        raise ValueError("Email newsletter manquant")

    db_subscription = NewsletterSubscriber(
        email=normalized_email,
        langue=data.get("langue"),
        source=data.get("source") or "crm",
        consentement=bool(data.get("consentement", True)),
        actif=True,
    )
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


def update_newsletter_subscription(
    db: Session,
    db_subscription: NewsletterSubscriber,
    payload: NewsletterSubscriptionUpdate,
) -> NewsletterSubscriber:
    updates = _model_dump(payload, exclude_unset=True)
    if "email" in updates and updates["email"] is not None:
        updates["email"] = normalize_newsletter_email(updates["email"])

    for key, value in updates.items():
        setattr(db_subscription, key, value)

    db.commit()
    db.refresh(db_subscription)
    return db_subscription


def delete_newsletter_subscription(db: Session, db_subscription: NewsletterSubscriber) -> None:
    db.delete(db_subscription)
    db.commit()
