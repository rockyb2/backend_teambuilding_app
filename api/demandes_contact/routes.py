from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import demande_contact as crud_demande_contact
from database.schemas import DemandeContactCreate, DemandeContactRead

router = APIRouter(prefix="/api/demandes-contact", tags=["demandes contact"])


@router.get("", response_model=List[DemandeContactRead])
def get_demandes_contact(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_demande_contact.get_demandes_contact(db, skip=skip, limit=limit)


@router.get("/{demande_id}", response_model=DemandeContactRead)
def get_demande_contact(demande_id: int, db: Session = Depends(get_db)):
    db_demande = crud_demande_contact.get_demande_contact(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande contact non trouvee")
    return db_demande


@router.post("", response_model=DemandeContactRead, status_code=status.HTTP_201_CREATED)
def create_demande_contact(payload: DemandeContactCreate, db: Session = Depends(get_db)):
    return crud_demande_contact.create_demande_contact(db, payload)
