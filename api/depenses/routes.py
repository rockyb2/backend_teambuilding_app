"""
Routes pour la gestion des depenses.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import activite as crud_activite
from crud import demande_team_building as crud_demande_team_building
from crud import demande_tourisme as crud_demande_tourisme
from crud import depense as crud_depense
from crud import facture as crud_facture
from crud import offre as crud_offre
from crud import proforma as crud_proforma
from crud import utilisateur as crud_utilisateur
from database.schemas import DepenseCreate, DepenseRead, DepenseUpdate
from security import require_financial_access

router = APIRouter(
    prefix="/api/depenses",
    tags=["depenses"],
    dependencies=[Depends(require_financial_access)],
)


def _payload_dump(payload, **kwargs):
    if hasattr(payload, "model_dump"):
        return payload.model_dump(**kwargs)
    return payload.dict(**kwargs)


def _validate_depense_relations(db: Session, data: dict):
    pole = data.get("pole") or "teambuilding"

    if data.get("categorie_depense_id") is not None:
        categorie = crud_depense.get_categorie_depense(db, data["categorie_depense_id"])
        if not categorie:
            raise HTTPException(status_code=404, detail="Categorie de depense non trouvee")

    if data.get("offre_id") is not None:
        if pole != "teambuilding":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Une offre team building doit etre liee a une depense teambuilding",
            )
        if not crud_offre.get_offre(db, data["offre_id"]):
            raise HTTPException(status_code=404, detail="Offre non trouvee")

    if data.get("activite_id") is not None:
        if pole != "teambuilding":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Une activite doit etre liee a une depense teambuilding",
            )
        if not crud_activite.get_activite(db, data["activite_id"]):
            raise HTTPException(status_code=404, detail="Activite non trouvee")

    if data.get("proforma_id") is not None:
        proforma = crud_proforma.get_proforma(db, data["proforma_id"])
        if not proforma:
            raise HTTPException(status_code=404, detail="Proforma non trouvee")
        if proforma.pole != pole:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le pole de la depense doit correspondre au pole de la proforma",
            )

    if data.get("facture_id") is not None:
        facture = crud_facture.get_facture(db, data["facture_id"])
        if not facture:
            raise HTTPException(status_code=404, detail="Facture non trouvee")
        if facture.pole != pole:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le pole de la depense doit correspondre au pole de la facture",
            )

    if data.get("demande_team_building_id") is not None:
        if pole != "teambuilding":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Une demande team building doit etre liee a une depense teambuilding",
            )
        if not crud_demande_team_building.get_demande_team_building(db, data["demande_team_building_id"]):
            raise HTTPException(status_code=404, detail="Demande team building non trouvee")

    if data.get("demande_tourisme_id") is not None:
        if pole != "tourisme":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Une demande tourisme doit etre liee a une depense tourisme",
            )
        if not crud_demande_tourisme.get_demande_tourisme(db, data["demande_tourisme_id"]):
            raise HTTPException(status_code=404, detail="Demande tourisme non trouvee")

    if data.get("demande_tourisme_custom_id") is not None:
        if pole != "tourisme":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Une demande tourisme personnalisee doit etre liee a une depense tourisme",
            )
        if not crud_demande_tourisme.get_demande_tourisme_custom(db, data["demande_tourisme_custom_id"]):
            raise HTTPException(status_code=404, detail="Demande tourisme personnalisee non trouvee")

    if data.get("id_utilisateur_cr") is not None:
        utilisateur = crud_utilisateur.get_utilisateur(db, data["id_utilisateur_cr"])
        if not utilisateur:
            raise HTTPException(status_code=404, detail="Utilisateur createur non trouve")


def _depense_context(db_depense) -> dict:
    return {
        "pole": db_depense.pole,
        "categorie_depense_id": db_depense.categorie_depense_id,
        "offre_id": db_depense.offre_id,
        "activite_id": db_depense.activite_id,
        "proforma_id": db_depense.proforma_id,
        "facture_id": db_depense.facture_id,
        "demande_team_building_id": db_depense.demande_team_building_id,
        "demande_tourisme_id": db_depense.demande_tourisme_id,
        "demande_tourisme_custom_id": db_depense.demande_tourisme_custom_id,
        "id_utilisateur_cr": db_depense.id_utilisateur_cr,
    }


@router.get("", response_model=List[DepenseRead])
def get_depenses(
    skip: int = 0,
    limit: int = 100,
    pole: str | None = None,
    facture_id: int | None = None,
    proforma_id: int | None = None,
    demande_team_building_id: int | None = None,
    demande_tourisme_id: int | None = None,
    demande_tourisme_custom_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Recuperer toutes les depenses."""
    return crud_depense.get_depenses(
        db,
        skip=skip,
        limit=limit,
        pole=pole,
        facture_id=facture_id,
        proforma_id=proforma_id,
        demande_team_building_id=demande_team_building_id,
        demande_tourisme_id=demande_tourisme_id,
        demande_tourisme_custom_id=demande_tourisme_custom_id,
    )


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
    current_user=Depends(require_financial_access),
):
    """Creer une nouvelle depense."""
    data = _payload_dump(payload)
    data["id_utilisateur_cr"] = getattr(current_user, "id_utilisateur", None)
    _validate_depense_relations(db, data)

    return crud_depense.create_depense(db, DepenseCreate(**data))


@router.put("/{depense_id}", response_model=DepenseRead)
def update_depense(depense_id: int, payload: DepenseUpdate, db: Session = Depends(get_db)):
    """Mettre a jour une depense."""
    db_depense = crud_depense.get_depense(db, depense_id)
    if not db_depense:
        raise HTTPException(status_code=404, detail="Depense non trouvee")

    updates = _payload_dump(payload, exclude_unset=True)
    if updates.get("pole") is None and "pole" in updates:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le pole de la depense est obligatoire",
        )
    context = _depense_context(db_depense)
    context.update(updates)
    _validate_depense_relations(db, context)

    return crud_depense.update_depense(db, db_depense, payload)


@router.delete("/{depense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_depense(depense_id: int, db: Session = Depends(get_db)):
    """Supprimer une depense."""
    db_depense = crud_depense.get_depense(db, depense_id)
    if not db_depense:
        raise HTTPException(status_code=404, detail="Depense non trouvee")

    crud_depense.delete_depense(db, db_depense)
