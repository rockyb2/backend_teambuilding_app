from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import demande_contact as crud_demande_contact
from database.schemas import DemandeContactCreate, DemandeContactRead
from services.email_service import build_contact_email, send_notification_email

router = APIRouter(prefix="/api/demandes-contact", tags=["demandes contact"])


def _send_contact_notification(subject: str, body: str, html_body: str | None = None) -> None:
    send_notification_email(subject=subject, body=body, html_body=html_body, profile="CONTACT")


@router.get("", response_model=List[DemandeContactRead])
def get_demandes_contact(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_demande_contact.get_demandes_contact(db, skip=skip, limit=limit)


@router.get("/{demande_id}", response_model=DemandeContactRead)
def get_demande_contact(demande_id: int, db: Session = Depends(get_db)):
    db_demande = crud_demande_contact.get_demande_contact(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande contact non trouvee")
    return db_demande


@router.post("", status_code=status.HTTP_201_CREATED)
def create_demande_contact(payload: dict, db: Session = Depends(get_db)):
    try:
        validated_payload = DemandeContactCreate(**payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    db_demande = crud_demande_contact.create_demande_contact(db, validated_payload)
    try:
        subject, body, html_body = build_contact_email(db_demande)
        _send_contact_notification(subject, body, html_body)
    except Exception as exc:
        print(f"Echec de l'envoi de l'email pour la demande contact {db_demande.id}: {exc}")
    return {
        "id": db_demande.id,
        "type": "contact",
        "message": "Demande contact enregistree",
    }
