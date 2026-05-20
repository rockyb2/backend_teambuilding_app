from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import benevole as crud_benevole
from database.schemas import BenevoleCreate, BenevoleRead, BenevoleUpdate
from security import require_module_access

router = APIRouter(
    prefix="/api/benevoles",
    tags=["benevoles"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


@router.get("", response_model=List[BenevoleRead])
def get_benevoles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_benevole.get_benevoles(db, skip=skip, limit=limit)


@router.get("/{benevole_id}", response_model=BenevoleRead)
def get_benevole(benevole_id: int, db: Session = Depends(get_db)):
    db_benevole = crud_benevole.get_benevole(db, benevole_id)
    if not db_benevole:
        raise HTTPException(status_code=404, detail="Benevole non trouve")
    return db_benevole


@router.post("", response_model=BenevoleRead, status_code=status.HTTP_201_CREATED)
def create_benevole(payload: BenevoleCreate, db: Session = Depends(get_db)):
    if not payload.email.strip():
        raise HTTPException(status_code=400, detail="Email obligatoire")

    existing = crud_benevole.get_benevole_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email deja utilise")

    return crud_benevole.create_benevole(db, payload)


@router.put("/{benevole_id}", response_model=BenevoleRead)
def update_benevole(benevole_id: int, payload: BenevoleUpdate, db: Session = Depends(get_db)):
    db_benevole = crud_benevole.get_benevole(db, benevole_id)
    if not db_benevole:
        raise HTTPException(status_code=404, detail="Benevole non trouve")

    updates = _model_dump(payload, exclude_unset=True)
    if "email" in updates:
        if not updates["email"] or not updates["email"].strip():
            raise HTTPException(status_code=400, detail="Email obligatoire")

    if "email" in updates and updates["email"] != db_benevole.email:
        existing = crud_benevole.get_benevole_by_email(db, updates["email"])
        if existing:
            raise HTTPException(status_code=400, detail="Email deja utilise")

    return crud_benevole.update_benevole(db, db_benevole, updates)


@router.delete("/{benevole_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_benevole(benevole_id: int, db: Session = Depends(get_db)):
    db_benevole = crud_benevole.get_benevole(db, benevole_id)
    if not db_benevole:
        raise HTTPException(status_code=404, detail="Benevole non trouve")

    crud_benevole.delete_benevole(db, db_benevole)
