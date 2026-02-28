"""
Routes pour la gestion des jeux
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from crud import jeu as crud_jeu
from database.schemas import JeuCreate, JeuRead
from api.dependencies import get_db

router = APIRouter(prefix="/api/jeux", tags=["jeux"])


@router.get("", response_model=List[JeuRead])
def get_jeux(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer tous les jeux"""
    return crud_jeu.get_jeus(db, skip=skip, limit=limit)


@router.get("/{jeu_id}", response_model=JeuRead)
def get_jeu(jeu_id: int, db: Session = Depends(get_db)):
    """Récupérer un jeu par ID"""
    db_jeu = crud_jeu.get_jeu(db, jeu_id)
    if not db_jeu:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    return db_jeu


@router.post("", response_model=JeuRead, status_code=status.HTTP_201_CREATED)
def create_jeu(payload: JeuCreate, db: Session = Depends(get_db)):
    """Créer un nouveau jeu"""
    return crud_jeu.create_jeu(db, payload)


@router.put("/{jeu_id}", response_model=JeuRead)
def update_jeu(jeu_id: int, payload: dict, db: Session = Depends(get_db)):
    """Mettre à jour un jeu"""
    db_jeu = crud_jeu.get_jeu(db, jeu_id)
    if not db_jeu:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    
    return crud_jeu.update_jeu(db, db_jeu, payload)


@router.delete("/{jeu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_jeu(jeu_id: int, db: Session = Depends(get_db)):
    """Supprimer un jeu"""
    db_jeu = crud_jeu.get_jeu(db, jeu_id)
    if not db_jeu:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    
    crud_jeu.delete_jeu(db, db_jeu)
