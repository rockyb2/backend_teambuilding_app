from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import demande_team_building as crud_demande_team_building
from database.schemas import DemandeTeamBuildingCreate, DemandeTeamBuildingRead
from services.email_service import build_team_building_email, send_notification_email
from security import get_user_role_name, require_module_access

router = APIRouter(prefix="/api/demandes-team-building", tags=["demandes team building"])


def _send_team_building_notification(subject: str, body: str, html_body: str | None = None) -> None:
    send_notification_email(subject=subject, body=body, html_body=html_body, profile="TEAMBUILDING")


def _ensure_can_delete_demande(current_user) -> None:
    if get_user_role_name(current_user) not in {"admin", "super_admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les admin et super_admin peuvent supprimer une demande",
        )


@router.get("", response_model=List[DemandeTeamBuildingRead])
def list_demandes_team_building(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    return crud_demande_team_building.get_demandes_team_building(db, skip=skip, limit=limit)


@router.get("/getDemande", response_model=List[DemandeTeamBuildingRead])
def get_demandes_team_building(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    return crud_demande_team_building.get_demandes_team_building(db, skip=skip, limit=limit)


@router.get("/{demande_id}", response_model=DemandeTeamBuildingRead)
def get_demande_team_building(
    demande_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    db_demande = crud_demande_team_building.get_demande_team_building(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande team building non trouvee")
    return db_demande


@router.patch("/{demande_id}/statut", response_model=DemandeTeamBuildingRead)
def update_demande_team_building_statut(
    demande_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    db_demande = crud_demande_team_building.get_demande_team_building(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande team building non trouvee")

    statut = payload.get("statut")
    if not statut:
        raise HTTPException(status_code=422, detail="Le statut est obligatoire")

    return crud_demande_team_building.update_demande_team_building_statut(db, db_demande, statut)


@router.delete("/{demande_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_demande_team_building(
    demande_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_module_access("teambuilding")),
):
    _ensure_can_delete_demande(current_user)
    db_demande = crud_demande_team_building.get_demande_team_building(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande team building non trouvee")
    crud_demande_team_building.delete_demande_team_building(db, db_demande)


@router.post("", response_model=DemandeTeamBuildingRead, status_code=status.HTTP_201_CREATED)
def create_demande_team_building(payload: DemandeTeamBuildingCreate, db: Session = Depends(get_db)):
    db_demande = crud_demande_team_building.create_demande_team_building(db, payload)
    try:
        subject, body, html_body = build_team_building_email(db_demande)
        _send_team_building_notification(subject, body, html_body)
    except Exception as exc:
        print(f"Echec de l'envoi de l'email pour la demande team building {db_demande.id}: {exc}")
    return db_demande
