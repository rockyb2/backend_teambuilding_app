from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import demande_tourisme as crud_demande_tourisme
from database.schemas import (
    DemandeTourismeCreate,
    DemandeTourismeCustom,
    DemandeTourismeRead,
    DemandeTourismeStatutUpdate,
    HistoriqueStatutDemandeTourismeRead,
)
from services.email_service import (
    build_custom_tourism_email,
    build_tourism_booking_email,
    send_notification_email,
)
from security import get_user_role_name, require_module_access

router = APIRouter(prefix="/api/demandes-tourisme", tags=["demandes tourisme"])


def _send_tourism_notification(subject: str, body: str, html_body: str | None = None) -> None:
    send_notification_email(subject=subject, body=body, html_body=html_body, profile="VOYAGE")


def _ensure_can_delete_demande(current_user) -> None:
    if get_user_role_name(current_user) not in {"admin", "super_admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les admin et super_admin peuvent supprimer une demande",
        )


@router.get("", response_model=List[DemandeTourismeRead])
def get_demandes_tourisme(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    return crud_demande_tourisme.get_demandes_tourisme(db, skip=skip, limit=limit)


@router.get("/custom", response_model=List[DemandeTourismeCustom])
def get_demandes_tourisme_custom(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    return crud_demande_tourisme.get_demandes_tourisme_custom(db, skip=skip, limit=limit)


@router.get("/custom/{demande_id}", response_model=DemandeTourismeCustom)
def get_demande_tourisme_custom(
    demande_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    db_demande = crud_demande_tourisme.get_demande_tourisme_custom(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande tourisme personnalisee non trouvee")
    return db_demande


@router.patch("/custom/{demande_id}/statut", response_model=DemandeTourismeCustom)
def update_demande_tourisme_custom_statut(
    demande_id: int,
    payload: DemandeTourismeStatutUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    db_demande = crud_demande_tourisme.get_demande_tourisme_custom(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande tourisme personnalisee non trouvee")

    try:
        return crud_demande_tourisme.update_demande_tourisme_custom_statut(
            db,
            db_demande,
            payload.statut,
            getattr(current_user, "id_utilisateur", None),
            payload.commentaire,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/custom/{demande_id}/historique",
    response_model=List[HistoriqueStatutDemandeTourismeRead],
)
def get_historique_demande_tourisme_custom(
    demande_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    db_demande = crud_demande_tourisme.get_demande_tourisme_custom(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande tourisme personnalisee non trouvee")
    return crud_demande_tourisme.get_historique_demande_tourisme_custom(db, demande_id)


@router.delete("/custom/{demande_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_demande_tourisme_custom(
    demande_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    _ensure_can_delete_demande(current_user)
    db_demande = crud_demande_tourisme.get_demande_tourisme_custom(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande tourisme personnalisee non trouvee")
    crud_demande_tourisme.delete_demande_tourisme_custom(db, db_demande)


@router.get("/{demande_id}", response_model=DemandeTourismeRead)
def get_demande_tourisme(
    demande_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    db_demande = crud_demande_tourisme.get_demande_tourisme(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande tourisme non trouvee")
    return db_demande


@router.patch("/{demande_id}/statut", response_model=DemandeTourismeRead)
def update_demande_tourisme_statut(
    demande_id: int,
    payload: DemandeTourismeStatutUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    db_demande = crud_demande_tourisme.get_demande_tourisme(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande tourisme non trouvee")

    try:
        return crud_demande_tourisme.update_demande_tourisme_statut(
            db,
            db_demande,
            payload.statut,
            getattr(current_user, "id_utilisateur", None),
            payload.commentaire,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get(
    "/{demande_id}/historique",
    response_model=List[HistoriqueStatutDemandeTourismeRead],
)
def get_historique_demande_tourisme(
    demande_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    db_demande = crud_demande_tourisme.get_demande_tourisme(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande tourisme non trouvee")
    return crud_demande_tourisme.get_historique_demande_tourisme(db, demande_id)


@router.delete("/{demande_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_demande_tourisme(
    demande_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("tourisme")),
):
    _ensure_can_delete_demande(current_user)
    db_demande = crud_demande_tourisme.get_demande_tourisme(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande tourisme non trouvee")
    crud_demande_tourisme.delete_demande_tourisme(db, db_demande)


@router.post("", response_model=DemandeTourismeRead, status_code=status.HTTP_201_CREATED)
def create_demande_tourisme(payload: DemandeTourismeCreate, db: Session = Depends(get_db)):
    db_demande = crud_demande_tourisme.create_demande_tourisme(db, payload)
    try:
        subject, body, html_body = build_tourism_booking_email(db_demande)
        _send_tourism_notification(subject, body, html_body)
    except Exception as exc:
        print(f"Echec de l'envoi de l'email pour la demande tourisme {db_demande.id}: {exc}")
    return db_demande

@router.post("/custom", response_model=DemandeTourismeCustom, status_code=status.HTTP_201_CREATED)
def create_demande_tourisme_custom(payload: dict, db: Session = Depends(get_db)):
    if not (payload.get("prenom") or payload.get("prenoms") or payload.get("prenoms_client")):
        raise HTTPException(status_code=422, detail="Le champ prenom/prenoms est requis")

    missing_fields = []
    if not (payload.get("nom") or payload.get("nom_client")):
        missing_fields.append("nom")
    if not (payload.get("email") or payload.get("email_client")):
        missing_fields.append("email")
    if not (payload.get("telephone") or payload.get("numero_telephone_client")):
        missing_fields.append("telephone")

    if missing_fields:
        raise HTTPException(
            status_code=422,
            detail=f"Champs requis manquants: {', '.join(missing_fields)}",
        )

    db_demande = crud_demande_tourisme.create_demande_tourisme_custom(db, payload)
    try:
        subject, body, html_body = build_custom_tourism_email(db_demande)
        _send_tourism_notification(subject, body, html_body)
    except Exception as exc:
        print(f"Echec de l'envoi de l'email pour la demande tourisme custom {db_demande.id}: {exc}")
    return db_demande
