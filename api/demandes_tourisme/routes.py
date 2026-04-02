from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import demande_tourisme as crud_demande_tourisme
from database.schemas import DemandeTourismeCreate, DemandeTourismeRead

router = APIRouter(prefix="/api/demandes-tourisme", tags=["demandes tourisme"])


@router.get("", response_model=List[DemandeTourismeRead])
def get_demandes_tourisme(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_demande_tourisme.get_demandes_tourisme(db, skip=skip, limit=limit)


@router.get("/{demande_id}", response_model=DemandeTourismeRead)
def get_demande_tourisme(demande_id: int, db: Session = Depends(get_db)):
    db_demande = crud_demande_tourisme.get_demande_tourisme(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande tourisme non trouvee")
    return db_demande


@router.post("", response_model=DemandeTourismeRead, status_code=status.HTTP_201_CREATED)
def create_demande_tourisme(payload: DemandeTourismeCreate, db: Session = Depends(get_db)):
    return crud_demande_tourisme.create_demande_tourisme(db, payload)
