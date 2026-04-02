from sqlalchemy.orm import Session
from database.models import ContactAkan
from database.schemas import ContactAkanCreate

def create_contact_akan(db: Session, contact: ContactAkanCreate):
    new_contact = ContactAkan(
        nom=contact.nom,
        prenoms=contact.prenoms,
        email=contact.email,
        telephone=contact.telephone
    )
    db.add(new_contact)
    db.commit()
    db.refresh(new_contact)
    return new_contact

def get_all_contacts_akan(db: Session):
    return db.query(ContactAkan).order_by(ContactAkan.id.desc()).all()

def get_contact_akan(db: Session, contact_id: int):
    return db.query(ContactAkan).filter(ContactAkan.id == contact_id).first()
