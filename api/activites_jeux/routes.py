"""
Routes pour la gestion des jeux associes aux activites.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import activite as crud_activite
from crud import activite_jeu as crud_activite_jeu
from crud import jeu as crud_jeu
from database.schemas import ActiviteJeuCreate, ActiviteJeuRead
from security import require_module_access

router = APIRouter(
    prefix="/api/activites_jeux",
    tags=["activites_jeux"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


@router.get("", response_model=List[ActiviteJeuRead])
def get_activites_jeux(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer toutes les associations activite-jeu."""
    return crud_activite_jeu.get_activites_jeux(db, skip=skip, limit=limit)


@router.get("/activites/{activite_id}", response_model=List[ActiviteJeuRead])
def get_jeux_of_activite(activite_id: int, db: Session = Depends(get_db)):
    """Recuperer les jeux d'une activite."""
    if not crud_activite.get_activite(db, activite_id):
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    return crud_activite_jeu.get_jeux_by_activite(db, activite_id)


@router.get("/{activite_id}/{jeu_id}", response_model=ActiviteJeuRead)
def get_activite_jeu(activite_id: int, jeu_id: int, db: Session = Depends(get_db)):
    """Recuperer une association activite-jeu."""
    db_activite_jeu = crud_activite_jeu.get_activite_jeu(db, activite_id, jeu_id)
    if not db_activite_jeu:
        raise HTTPException(status_code=404, detail="Association non trouvee")
    return db_activite_jeu


@router.post("", response_model=ActiviteJeuRead, status_code=status.HTTP_201_CREATED)
def create_activite_jeu(
    payload: ActiviteJeuCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Creer une association activite-jeu."""
    if not crud_activite.get_activite(db, payload.activite_id):
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    if not crud_jeu.get_jeu(db, payload.jeu_id):
        raise HTTPException(status_code=404, detail="Jeu non trouve")

    existing = crud_activite_jeu.get_activite_jeu(db, payload.activite_id, payload.jeu_id)
    if existing:
        raise HTTPException(status_code=409, detail="Cette association existe deja")

    payload.id_utilisateur_create = getattr(current_user, "id_utilisateur", None)
    return crud_activite_jeu.create_activite_jeu(db, payload)


@router.put("/{activite_id}/{jeu_id}", response_model=ActiviteJeuRead)
def update_activite_jeu(activite_id: int, jeu_id: int, payload: dict, db: Session = Depends(get_db)):
    """Mettre a jour une association activite-jeu."""
    db_activite_jeu = crud_activite_jeu.get_activite_jeu(db, activite_id, jeu_id)
    if not db_activite_jeu:
        raise HTTPException(status_code=404, detail="Association non trouvee")

    return crud_activite_jeu.update_activite_jeu(db, db_activite_jeu, payload)


@router.delete("/{activite_id}/{jeu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activite_jeu(activite_id: int, jeu_id: int, db: Session = Depends(get_db)):
    """Supprimer une association activite-jeu."""
    db_activite_jeu = crud_activite_jeu.get_activite_jeu(db, activite_id, jeu_id)
    if not db_activite_jeu:
        raise HTTPException(status_code=404, detail="Association non trouvee")

    crud_activite_jeu.delete_activite_jeu(db, db_activite_jeu)
