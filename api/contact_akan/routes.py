from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.schemas import ContactAkanCreate, ContactAkanResponse
from crud.contact_akan import create_contact_akan, get_all_contacts_akan, get_contact_akan, tirer_au_sort_contact

router = APIRouter(prefix="/contact-akan", tags=["Contact Akan"])

@router.post("/ajouter", response_model=ContactAkanResponse)
def create_contact(contact: ContactAkanCreate, db: Session = Depends(get_db)):
    return create_contact_akan(db, contact)

@router.get("/liste", response_model=list[ContactAkanResponse])
def list_contacts(db: Session = Depends(get_db)):
    return get_all_contacts_akan(db)

@router.get("/{contact_id}", response_model=ContactAkanResponse)
def read_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = get_contact_akan(db, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact introuvable")
    return contact

@router.post("/contact-akan/tirage-au-sort", response_model=ContactAkanResponse)
def tirage_au_sort(db: Session = Depends(get_db)):
    gagnant = tirer_au_sort_contact(db)
    if not gagnant:
        raise HTTPException(status_code=404, detail="Aucun contact disponible pour le tirage")
    return gagnant