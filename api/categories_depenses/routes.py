"""
Routes pour la gestion des categories de depenses.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import depense as crud_depense
from database.schemas import CategorieDepenseCreate, CategorieDepenseRead, CategorieDepenseUpdate
from security import require_financial_access

router = APIRouter(
    prefix="/api/categories-depenses",
    tags=["categories_depenses"],
    dependencies=[Depends(require_financial_access)],
)


@router.get("", response_model=List[CategorieDepenseRead])
def get_categories_depenses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer les categories de depenses."""
    return crud_depense.get_categories_depenses(db, skip=skip, limit=limit)


@router.get("/{categorie_id}", response_model=CategorieDepenseRead)
def get_categorie_depense(categorie_id: int, db: Session = Depends(get_db)):
    """Recuperer une categorie de depense."""
    db_categorie = crud_depense.get_categorie_depense(db, categorie_id)
    if not db_categorie:
        raise HTTPException(status_code=404, detail="Categorie de depense non trouvee")
    return db_categorie


@router.post("", response_model=CategorieDepenseRead, status_code=status.HTTP_201_CREATED)
def create_categorie_depense(payload: CategorieDepenseCreate, db: Session = Depends(get_db)):
    """Creer une categorie de depense."""
    existing = crud_depense.get_categorie_depense_by_nom(db, payload.nom)
    if existing:
        raise HTTPException(status_code=409, detail="Categorie de depense deja existante")

    return crud_depense.create_categorie_depense(db, payload)


@router.put("/{categorie_id}", response_model=CategorieDepenseRead)
def update_categorie_depense(categorie_id: int, payload: CategorieDepenseUpdate, db: Session = Depends(get_db)):
    """Mettre a jour une categorie de depense."""
    db_categorie = crud_depense.get_categorie_depense(db, categorie_id)
    if not db_categorie:
        raise HTTPException(status_code=404, detail="Categorie de depense non trouvee")

    updates = payload.model_dump(exclude_unset=True) if hasattr(payload, "model_dump") else payload.dict(exclude_unset=True)
    if "nom" in updates and updates["nom"] and updates["nom"] != db_categorie.nom:
        existing = crud_depense.get_categorie_depense_by_nom(db, updates["nom"])
        if existing:
            raise HTTPException(status_code=409, detail="Categorie de depense deja existante")

    return crud_depense.update_categorie_depense(db, db_categorie, payload)


@router.delete("/{categorie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categorie_depense(categorie_id: int, db: Session = Depends(get_db)):
    """Supprimer une categorie de depense."""
    db_categorie = crud_depense.get_categorie_depense(db, categorie_id)
    if not db_categorie:
        raise HTTPException(status_code=404, detail="Categorie de depense non trouvee")

    crud_depense.delete_categorie_depense(db, db_categorie)
