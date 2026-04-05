from sqlalchemy.orm import Session
from database.models import ContactAkan
from database.schemas import ContactAkanCreate
import random

def create_contact_akan(db: Session, contact: ContactAkanCreate):
    new_contact = ContactAkan(
        nom=contact.nom,
        prenoms=contact.prenoms,
        email=contact.email,
        telephone=contact.telephone,
        has_won=contact.has_won or False
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact

def get_all_contacts_akan(db: Session):
    return db.query(ContactAkan).order_by(ContactAkan.id.desc()).all()

def get_available_contacts_akan(db: Session):
    return db.query(ContactAkan).filter((ContactAkan.has_won == False) | (ContactAkan.has_won == None)).all()

def get_contact_akan(db: Session, contact_id: int):
    return db.query(ContactAkan).filter(ContactAkan.id == contact_id).first()

def tirer_au_sort_contact(db: Session):
    contacts = get_available_contacts_akan(db)
    if not contacts:
        return None
    gagnant = random.choice(contacts)
    gagnant.has_won = True
    db.add(gagnant)
    db.commit()
    db.refresh(gagnant)
    return gagnant
