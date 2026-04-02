from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import demande_team_building as crud_demande_team_building
from database.schemas import DemandeTeamBuildingCreate, DemandeTeamBuildingRead

router = APIRouter(prefix="/api/demandes-team-building", tags=["demandes team building"])


@router.get("", response_model=List[DemandeTeamBuildingRead])
def get_demandes_team_building(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud_demande_team_building.get_demandes_team_building(db, skip=skip, limit=limit)


@router.get("/{demande_id}", response_model=DemandeTeamBuildingRead)
def get_demande_team_building(demande_id: int, db: Session = Depends(get_db)):
    db_demande = crud_demande_team_building.get_demande_team_building(db, demande_id)
    if not db_demande:
        raise HTTPException(status_code=404, detail="Demande team building non trouvee")
    return db_demande


@router.post("", response_model=DemandeTeamBuildingRead, status_code=status.HTTP_201_CREATED)
def create_demande_team_building(payload: DemandeTeamBuildingCreate, db: Session = Depends(get_db)):
    return crud_demande_team_building.create_demande_team_building(db, payload)
