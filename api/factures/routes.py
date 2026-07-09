from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import demande_team_building as crud_demande_team_building
from crud import demande_tourisme as crud_demande_tourisme
from crud import facture as crud_facture
from crud import proforma as crud_proforma
from database.schemas import (
    FactureCreate,
    FactureRead,
    FactureUpdate,
    PaiementCreate,
    PaiementRead,
    PaiementUpdate,
)
from security import get_current_user, require_financial_access


router = APIRouter(
    prefix="/api/factures",
    tags=["factures"],
    dependencies=[Depends(require_financial_access)],
)


def _payload_dump(payload, **kwargs):
    if hasattr(payload, "model_dump"):
        return payload.model_dump(**kwargs)
    return payload.dict(**kwargs)


def _validate_facture_relations(db: Session, data: dict) -> None:
    pole = data.get("pole")

    proforma = None
    if data.get("proforma_id") is not None:
        proforma = crud_proforma.get_proforma(db, data["proforma_id"])
        if not proforma:
            raise HTTPException(status_code=404, detail="Proforma non trouvee")

    if data.get("demande_team_building_id") is not None:
        if not crud_demande_team_building.get_demande_team_building(db, data["demande_team_building_id"]):
            raise HTTPException(status_code=404, detail="Demande team building non trouvee")

    if data.get("demande_tourisme_id") is not None:
        if not crud_demande_tourisme.get_demande_tourisme(db, data["demande_tourisme_id"]):
            raise HTTPException(status_code=404, detail="Demande tourisme non trouvee")

    if data.get("demande_tourisme_custom_id") is not None:
        if not crud_demande_tourisme.get_demande_tourisme_custom(db, data["demande_tourisme_custom_id"]):
            raise HTTPException(status_code=404, detail="Demande tourisme personnalisee non trouvee")

    if proforma and pole and proforma.pole != pole:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le pole de la facture doit correspondre au pole de la proforma",
        )

    if data.get("demande_team_building_id") is not None and pole != "teambuilding":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Une demande team building doit etre liee a une facture teambuilding",
        )

    has_tourism_context = data.get("demande_tourisme_id") is not None or data.get("demande_tourisme_custom_id") is not None
    if has_tourism_context and pole != "tourisme":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Une demande tourisme doit etre liee a une facture tourisme",
        )


def _facture_context(db_facture) -> dict:
    return {
        "pole": db_facture.pole,
        "proforma_id": db_facture.proforma_id,
        "demande_team_building_id": db_facture.demande_team_building_id,
        "demande_tourisme_id": db_facture.demande_tourisme_id,
        "demande_tourisme_custom_id": db_facture.demande_tourisme_custom_id,
    }


def _get_facture_or_404(db: Session, facture_id: int):
    db_facture = crud_facture.get_facture(db, facture_id)
    if not db_facture:
        raise HTTPException(status_code=404, detail="Facture non trouvee")
    return db_facture


def _get_paiement_or_404(db: Session, paiement_id: int):
    db_paiement = crud_facture.get_paiement(db, paiement_id)
    if not db_paiement:
        raise HTTPException(status_code=404, detail="Paiement non trouve")
    return db_paiement


@router.get("", response_model=List[FactureRead])
def list_factures(
    skip: int = 0,
    limit: int = 100,
    pole: str | None = None,
    statut: str | None = None,
    db: Session = Depends(get_db),
):
    return crud_facture.get_factures(db, skip=skip, limit=limit, pole=pole, statut=statut)


@router.post("", response_model=FactureRead, status_code=status.HTTP_201_CREATED)
def create_facture(
    payload: FactureCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    data = _payload_dump(payload)
    _validate_facture_relations(db, data)
    try:
        return crud_facture.create_facture(
            db,
            payload,
            created_by_id=getattr(current_user, "id_utilisateur", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/from-proforma/{proforma_id}", response_model=FactureRead, status_code=status.HTTP_201_CREATED)
def create_facture_from_proforma(
    proforma_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_proforma = crud_proforma.get_proforma(db, proforma_id)
    if not db_proforma:
        raise HTTPException(status_code=404, detail="Proforma non trouvee")
    try:
        return crud_facture.create_facture_from_proforma(
            db,
            db_proforma,
            created_by_id=getattr(current_user, "id_utilisateur", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/paiements/{paiement_id}", response_model=PaiementRead)
def get_paiement(paiement_id: int, db: Session = Depends(get_db)):
    return _get_paiement_or_404(db, paiement_id)


@router.put("/paiements/{paiement_id}", response_model=PaiementRead)
def update_paiement(
    paiement_id: int,
    payload: PaiementUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_paiement = _get_paiement_or_404(db, paiement_id)
    try:
        return crud_facture.update_paiement(
            db,
            db_paiement,
            payload,
            updated_by_id=getattr(current_user, "id_utilisateur", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.delete("/paiements/{paiement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_paiement(paiement_id: int, db: Session = Depends(get_db)):
    db_paiement = _get_paiement_or_404(db, paiement_id)
    crud_facture.delete_paiement(db, db_paiement)


@router.get("/{facture_id}", response_model=FactureRead)
def get_facture(facture_id: int, db: Session = Depends(get_db)):
    return _get_facture_or_404(db, facture_id)


@router.put("/{facture_id}", response_model=FactureRead)
def update_facture(
    facture_id: int,
    payload: FactureUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_facture = _get_facture_or_404(db, facture_id)
    updates = _payload_dump(payload, exclude_unset=True)
    context = _facture_context(db_facture)
    context.update(updates)
    _validate_facture_relations(db, context)
    try:
        return crud_facture.update_facture(
            db,
            db_facture,
            payload,
            updated_by_id=getattr(current_user, "id_utilisateur", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.patch("/{facture_id}/annuler", response_model=FactureRead)
def annuler_facture(
    facture_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_facture = _get_facture_or_404(db, facture_id)
    try:
        return crud_facture.annuler_facture(
            db,
            db_facture,
            updated_by_id=getattr(current_user, "id_utilisateur", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/{facture_id}/paiements", response_model=List[PaiementRead])
def list_paiements_facture(
    facture_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    _get_facture_or_404(db, facture_id)
    return crud_facture.get_paiements_by_facture(db, facture_id, skip=skip, limit=limit)


@router.post("/{facture_id}/paiements", response_model=PaiementRead, status_code=status.HTTP_201_CREATED)
def create_paiement(
    facture_id: int,
    payload: PaiementCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db_facture = _get_facture_or_404(db, facture_id)
    try:
        return crud_facture.create_paiement(
            db,
            db_facture,
            payload,
            created_by_id=getattr(current_user, "id_utilisateur", None),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
