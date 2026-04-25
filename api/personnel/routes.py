"""
Routes pour la gestion du personnel
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import personnel as crud_personnel
from database.schemas import PersonnelCreate, PersonnelRead, PersonnelUpdate
from security import require_module_access

router = APIRouter(
    prefix="/api/personnel",
    tags=["personnel"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


@router.get("", response_model=List[PersonnelRead])
def get_personnels(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer tout le personnel"""
    return crud_personnel.get_personnels(db, skip=skip, limit=limit)


@router.get("/disponibles", response_model=List[PersonnelRead])
def get_personnels_disponibles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer le personnel disponible"""
    return crud_personnel.get_personnels_disponibles(db, skip=skip, limit=limit)


@router.get("/{personnel_id}", response_model=PersonnelRead)
def get_personnel(personnel_id: int, db: Session = Depends(get_db)):
    """Recuperer un membre du personnel par ID"""
    db_personnel = crud_personnel.get_personnel(db, personnel_id)
    if not db_personnel:
        raise HTTPException(status_code=404, detail="Personnel non trouve")
    return db_personnel


@router.post("", response_model=PersonnelRead, status_code=status.HTTP_201_CREATED)
def create_personnel(payload: PersonnelCreate, db: Session = Depends(get_db)):
    """Creer un nouveau membre du personnel"""
    if payload.email:
        existing = crud_personnel.get_personnel_by_email(db, payload.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email deja utilise")

    return crud_personnel.create_personnel(db, payload)


@router.put("/{personnel_id}", response_model=PersonnelRead)
def update_personnel(personnel_id: int, payload: PersonnelUpdate, db: Session = Depends(get_db)):
    """Mettre a jour un membre du personnel"""
    db_personnel = crud_personnel.get_personnel(db, personnel_id)
    if not db_personnel:
        raise HTTPException(status_code=404, detail="Personnel non trouve")

    updates = payload.model_dump(exclude_unset=True)
    if "email" in updates and updates["email"] and updates["email"] != db_personnel.email:
        existing = crud_personnel.get_personnel_by_email(db, updates["email"])
        if existing:
            raise HTTPException(status_code=400, detail="Email deja utilise")

    return crud_personnel.update_personnel(db, db_personnel, updates)


@router.delete("/{personnel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_personnel(personnel_id: int, db: Session = Depends(get_db)):
    """Supprimer un membre du personnel"""
    db_personnel = crud_personnel.get_personnel(db, personnel_id)
    if not db_personnel:
        raise HTTPException(status_code=404, detail="Personnel non trouve")

    crud_personnel.delete_personnel(db, db_personnel)
