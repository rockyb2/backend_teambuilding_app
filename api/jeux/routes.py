"""
Routes pour la gestion des jeux
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from crud import jeu as crud_jeu
from crud import materiel as crud_materiel
from database.schemas import JeuCreate, JeuRead, JeuUpdate
from api.dependencies import get_db
from security import require_module_access

router = APIRouter(
    prefix="/api/jeux",
    tags=["jeux"],
    dependencies=[Depends(require_module_access("teambuilding"))],
)


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def _validate_materiels_requis(db: Session, materiels: list) -> None:
    for materiel_payload in materiels or []:
        data = _model_dump(materiel_payload) if hasattr(materiel_payload, "dict") else dict(materiel_payload)
        materiel_id = int(data["materiel_id"])
        quantite_requise = int(data.get("quantite_requise") or 1)

        db_materiel = crud_materiel.get_materiel(db, materiel_id)
        if not db_materiel:
            raise HTTPException(status_code=404, detail="Materiel non trouve")
        if db_materiel.statut is False:
            raise HTTPException(
                status_code=400,
                detail=f"Materiel inactif: {db_materiel.nom} ne peut pas etre requis pour un jeu",
            )

        stock_total = int(db_materiel.quantite_disponible or 0)
        if quantite_requise > stock_total:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Quantite requise trop elevee pour {db_materiel.nom}: "
                    f"{stock_total} unite(s) en stock total"
                ),
            )


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
def create_jeu(
    payload: JeuCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    """Créer un nouveau jeu"""
    payload.id_utilisateur_create = getattr(current_user, "id_utilisateur", None)
    _validate_materiels_requis(db, payload.materiels)
    return crud_jeu.create_jeu(db, payload)


@router.put("/{jeu_id}", response_model=JeuRead)
def update_jeu(jeu_id: int, payload: JeuUpdate, db: Session = Depends(get_db)):
    """Mettre à jour un jeu"""
    db_jeu = crud_jeu.get_jeu(db, jeu_id)
    if not db_jeu:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    
    updates = _model_dump(payload, exclude_unset=True)
    if "materiels" in updates:
        _validate_materiels_requis(db, updates["materiels"])

    return crud_jeu.update_jeu(db, db_jeu, payload)


@router.delete("/{jeu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_jeu(jeu_id: int, db: Session = Depends(get_db)):
    """Supprimer un jeu"""
    db_jeu = crud_jeu.get_jeu(db, jeu_id)
    if not db_jeu:
        raise HTTPException(status_code=404, detail="Jeu non trouvé")
    
    crud_jeu.delete_jeu(db, db_jeu)
