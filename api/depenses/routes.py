"""
Routes pour la gestion des depenses.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import activite as crud_activite
from crud import depense as crud_depense
from crud import offre as crud_offre
from crud import utilisateur as crud_utilisateur
from database.schemas import DepenseCreate, DepenseRead, DepenseUpdate
from security import require_financial_access, require_module_access

router = APIRouter(
    prefix="/api/depenses",
    tags=["depenses"],
    dependencies=[
        Depends(require_module_access("teambuilding")),
        Depends(require_financial_access),
    ],
)


def _payload_dump(payload, **kwargs):
    if hasattr(payload, "model_dump"):
        return payload.model_dump(**kwargs)
    return payload.dict(**kwargs)


def _validate_depense_relations(db: Session, data: dict):
    if data.get("categorie_depense_id") is not None:
        categorie = crud_depense.get_categorie_depense(db, data["categorie_depense_id"])
        if not categorie:
            raise HTTPException(status_code=404, detail="Categorie de depense non trouvee")

    if data.get("offre_id") is not None and not crud_offre.get_offre(db, data["offre_id"]):
        raise HTTPException(status_code=404, detail="Offre non trouvee")

    if data.get("activite_id") is not None and not crud_activite.get_activite(db, data["activite_id"]):
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    if data.get("id_utilisateur_cr") is not None:
        utilisateur = crud_utilisateur.get_utilisateur(db, data["id_utilisateur_cr"])
        if not utilisateur:
            raise HTTPException(status_code=404, detail="Utilisateur createur non trouve")


@router.get("", response_model=List[DepenseRead])
def get_depenses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer toutes les depenses."""
    return crud_depense.get_depenses(db, skip=skip, limit=limit)


@router.get("/activites/{activite_id}", response_model=List[DepenseRead])
def get_depenses_by_activite(activite_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer les depenses d'une activite."""
    if not crud_activite.get_activite(db, activite_id):
        raise HTTPException(status_code=404, detail="Activite non trouvee")

    return crud_depense.get_depenses_by_activite(db, activite_id, skip=skip, limit=limit)


@router.get("/offres/{offre_id}", response_model=List[DepenseRead])
def get_depenses_by_offre(offre_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer les depenses d'une offre."""
    if not crud_offre.get_offre(db, offre_id):
        raise HTTPException(status_code=404, detail="Offre non trouvee")

    return crud_depense.get_depenses_by_offre(db, offre_id, skip=skip, limit=limit)


@router.get("/categories/{categorie_id}", response_model=List[DepenseRead])
def get_depenses_by_categorie(categorie_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Recuperer les depenses d'une categorie."""
    if not crud_depense.get_categorie_depense(db, categorie_id):
        raise HTTPException(status_code=404, detail="Categorie de depense non trouvee")

    return crud_depense.get_depenses_by_categorie(db, categorie_id, skip=skip, limit=limit)


@router.get("/{depense_id}", response_model=DepenseRead)
def get_depense(depense_id: int, db: Session = Depends(get_db)):
    """Recuperer une depense par ID."""
    db_depense = crud_depense.get_depense(db, depense_id)
    if not db_depense:
        raise HTTPException(status_code=404, detail="Depense non trouvee")
    return db_depense


@router.post("", response_model=DepenseRead, status_code=status.HTTP_201_CREATED)
def create_depense(
    payload: DepenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Creer une nouvelle depense."""
    payload.id_utilisateur_cr = getattr(current_user, "id_utilisateur", None)
    data = _payload_dump(payload)
    _validate_depense_relations(db, data)

    return crud_depense.create_depense(db, payload)


@router.put("/{depense_id}", response_model=DepenseRead)
def update_depense(depense_id: int, payload: DepenseUpdate, db: Session = Depends(get_db)):
    """Mettre a jour une depense."""
    db_depense = crud_depense.get_depense(db, depense_id)
    if not db_depense:
        raise HTTPException(status_code=404, detail="Depense non trouvee")

    updates = _payload_dump(payload, exclude_unset=True)
    _validate_depense_relations(db, updates)

    return crud_depense.update_depense(db, db_depense, payload)


@router.delete("/{depense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_depense(depense_id: int, db: Session = Depends(get_db)):
    """Supprimer une depense."""
    db_depense = crud_depense.get_depense(db, depense_id)
    if not db_depense:
        raise HTTPException(status_code=404, detail="Depense non trouvee")

    crud_depense.delete_depense(db, db_depense)
