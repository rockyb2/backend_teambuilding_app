import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import newsletter as crud_newsletter
from database.schemas import NewsletterSubscriptionCreate, NewsletterSubscriptionRead, NewsletterSubscriptionUpdate
from security import require_module_access
from services.email_service import build_newsletter_subscription_email, send_notification_email

router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _build_newsletter_payload(payload: dict) -> NewsletterSubscriptionCreate:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Payload newsletter invalide")

    email = str(payload.get("email", "")).strip().lower()
    if not EMAIL_PATTERN.match(email):
        raise HTTPException(status_code=422, detail="Email newsletter invalide")

    raw_langue = payload.get("langue")
    langue = str(raw_langue).strip().lower()[:10] if raw_langue else None

    raw_source = payload.get("source") or "site_web"
    source = str(raw_source).strip()[:50] or "site_web"

    try:
        return NewsletterSubscriptionCreate(
            email=email,
            langue=langue,
            source=source,
            consentement=bool(payload.get("consentement", True)),
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _build_newsletter_update_payload(payload: dict) -> NewsletterSubscriptionUpdate:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Payload newsletter invalide")

    allowed_fields = {"email", "langue", "source", "consentement", "actif"}
    data = {key: payload[key] for key in allowed_fields if key in payload}
    if not data:
        raise HTTPException(status_code=422, detail="Aucun champ newsletter a mettre a jour")

    if "email" in data and data["email"] is not None:
        email = str(data["email"]).strip().lower()
        if not EMAIL_PATTERN.match(email):
            raise HTTPException(status_code=422, detail="Email newsletter invalide")
        data["email"] = email

    if "langue" in data and data["langue"] is not None:
        data["langue"] = str(data["langue"]).strip().lower()[:10] or None

    if "source" in data and data["source"] is not None:
        data["source"] = str(data["source"]).strip()[:50] or "crm"

    try:
        return NewsletterSubscriptionUpdate(**data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _send_newsletter_notification(db_subscription) -> None:
    subject, body, html_body = build_newsletter_subscription_email(db_subscription)
    send_notification_email(subject=subject, body=body, html_body=html_body, profile="NEWSLETTER")


@router.get("", response_model=List[NewsletterSubscriptionRead])
def get_newsletter_subscriptions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("administration")),
):
    return crud_newsletter.get_newsletter_subscriptions(db, skip=skip, limit=limit)


@router.post("/subscribe", status_code=status.HTTP_201_CREATED)
def subscribe_newsletter(payload: dict, db: Session = Depends(get_db)):
    validated_payload = _build_newsletter_payload(payload)

    db_subscription, created = crud_newsletter.create_or_update_newsletter_subscription(db, validated_payload)
    if created:
        try:
            _send_newsletter_notification(db_subscription)
        except Exception as exc:
            print(f"Echec de l'envoi de l'email pour l'inscription newsletter {db_subscription.id}: {exc}")

    return {
        "id": db_subscription.id,
        "type": "newsletter",
        "created": created,
        "message": "Inscription newsletter enregistree",
    }


@router.post("", response_model=NewsletterSubscriptionRead, status_code=status.HTTP_201_CREATED)
def create_newsletter_subscription(
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("administration")),
):
    validated_payload = _build_newsletter_payload(payload)
    existing_subscription = crud_newsletter.get_newsletter_subscription_by_email(db, validated_payload.email)
    if existing_subscription:
        raise HTTPException(status_code=400, detail="Cet email est deja inscrit a la newsletter")

    db_subscription = crud_newsletter.create_newsletter_subscription(db, validated_payload)
    if "actif" in payload:
        return crud_newsletter.update_newsletter_subscription(
            db,
            db_subscription,
            NewsletterSubscriptionUpdate(actif=bool(payload.get("actif"))),
        )
    return db_subscription


@router.get("/{subscription_id}", response_model=NewsletterSubscriptionRead)
def get_newsletter_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("administration")),
):
    db_subscription = crud_newsletter.get_newsletter_subscription(db, subscription_id)
    if not db_subscription:
        raise HTTPException(status_code=404, detail="Inscription newsletter non trouvee")
    return db_subscription


@router.put("/{subscription_id}", response_model=NewsletterSubscriptionRead)
def update_newsletter_subscription(
    subscription_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("administration")),
):
    db_subscription = crud_newsletter.get_newsletter_subscription(db, subscription_id)
    if not db_subscription:
        raise HTTPException(status_code=404, detail="Inscription newsletter non trouvee")

    validated_payload = _build_newsletter_update_payload(payload)
    if validated_payload.email and validated_payload.email != db_subscription.email:
        existing_subscription = crud_newsletter.get_newsletter_subscription_by_email(db, validated_payload.email)
        if existing_subscription:
            raise HTTPException(status_code=400, detail="Cet email est deja inscrit a la newsletter")

    return crud_newsletter.update_newsletter_subscription(db, db_subscription, validated_payload)


@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_newsletter_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("administration")),
):
    db_subscription = crud_newsletter.get_newsletter_subscription(db, subscription_id)
    if not db_subscription:
        raise HTTPException(status_code=404, detail="Inscription newsletter non trouvee")

    crud_newsletter.delete_newsletter_subscription(db, db_subscription)
