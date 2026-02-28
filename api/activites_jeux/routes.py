"""
Routes pour la gestion des associations activité-jeu
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from crud import activite_jeu as crud_activite_jeu
from crud import activite as crud_activite
from crud import jeu as crud_jeu
from database.schemas import ActiviteJeuCreate, ActiviteJeuRead
from api.dependencies import get_db

router = APIRouter(prefix="/api/activites_jeux", tags=["activites_jeux"])


@router.get("", response_model=List[ActiviteJeuRead])
def get_activites_jeux(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Récupérer toutes les associations activité-jeu"""
    return db.query(__import__('database.models', fromlist=['ActiviteJeu']).ActiviteJeu).offset(skip).limit(limit).all()


@router.get("/activites/{activite_id}", response_model=List[ActiviteJeuRead])
def get_jeux_of_activite(activite_id: int, db: Session = Depends(get_db)):
    """Récupérer les jeux d'une activité"""
    activite = crud_activite.get_activite(db, activite_id)
    if not activite:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    
    return crud_activite_jeu.get_jeux_by_activite(db, activite_id)


@router.get("/{activite_id}/{jeu_id}", response_model=ActiviteJeuRead)
def get_activite_jeu(activite_id: int, jeu_id: int, db: Session = Depends(get_db)):
    """Récupérer une association activité-jeu"""
    db_activite_jeu = crud_activite_jeu.get_activite_jeu(db, activite_id, jeu_id)
    if not db_activite_jeu:
        raise HTTPException(status_code=404, detail="Association non trouvée")
    return db_activite_jeu


@router.post("", response_model=ActiviteJeuRead, status_code=status.HTTP_201_CREATED)
def create_activite_jeu(payload: ActiviteJeuCreate, db: Session = Depends(get_db)):
    """Créer une association activité-jeu"""
    # Vérifier que l'activité existe
    activite = crud_activite.get_activite(db, payload.id_activite)
    if not activite:
        raise HTTPException(status_code=404, detail="Activité non trouvée")
    
    # Vérifier que le jeu existe
    jeu = crud_jeu.get_jeu(db, payload.id_jeu)
    if not jeu:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    
    # Vérifier que l'association n'existe pas déjà
    existing = crud_activite_jeu.get_activite_jeu(db, payload.id_activite, payload.id_jeu)
    if existing:
        raise HTTPException(status_code=400, detail="Cette association existe déjà")
    
    return crud_activite_jeu.create_activite_jeu(db, payload)


@router.put("/{activite_id}/{jeu_id}", response_model=ActiviteJeuRead)
def update_activite_jeu(activite_id: int, jeu_id: int, payload: dict, db: Session = Depends(get_db)):
    """Mettre à jour une association activité-jeu"""
    db_activite_jeu = crud_activite_jeu.get_activite_jeu(db, activite_id, jeu_id)
    if not db_activite_jeu:
        raise HTTPException(status_code=404, detail="Association non trouvée")
    
    return crud_activite_jeu.update_activite_jeu(db, db_activite_jeu, payload)


@router.delete("/{activite_id}/{jeu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activite_jeu(activite_id: int, jeu_id: int, db: Session = Depends(get_db)):
    """Supprimer une association activité-jeu"""
    db_activite_jeu = crud_activite_jeu.get_activite_jeu(db, activite_id, jeu_id)
    if not db_activite_jeu:
        raise HTTPException(status_code=404, detail="Association non trouvée")
    
    crud_activite_jeu.delete_activite_jeu(db, db_activite_jeu)
