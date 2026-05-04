from typing import Optional

from sqlalchemy.orm import Session, selectinload

from database.models import DemandeTeamBuilding, DemandeTeamBuildingCadre
from database.schemas import DemandeTeamBuildingCreate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_demande_team_building(db: Session, demande_id: int) -> Optional[DemandeTeamBuilding]:
    return (
        db.query(DemandeTeamBuilding)
        .options(selectinload(DemandeTeamBuilding.cadres))
        .filter(DemandeTeamBuilding.id == demande_id)
        .first()
    )


def get_demandes_team_building(
    db: Session, skip: int = 0, limit: int = 100
) -> list[DemandeTeamBuilding]:
    return (
        db.query(DemandeTeamBuilding)
        .options(selectinload(DemandeTeamBuilding.cadres))
        .order_by(DemandeTeamBuilding.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_demande_team_building(
    db: Session, payload: DemandeTeamBuildingCreate
) -> DemandeTeamBuilding:
    data = _model_dump(payload)
    cadres = data.pop("cadres", [])

    db_demande = DemandeTeamBuilding(**data)
    for cadre in cadres:
        db_demande.cadres.append(DemandeTeamBuildingCadre(cadre=cadre["cadre"]))

    db.add(db_demande)
    db.commit()
    db.refresh(db_demande)
    return get_demande_team_building(db, db_demande.id)


def update_demande_team_building(
    db: Session,
    db_demande: DemandeTeamBuilding,
    payload: DemandeTeamBuildingCreate | dict,
) -> DemandeTeamBuilding:
    data = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    cadres = data.pop("cadres", None)

    for key, value in data.items():
        if hasattr(db_demande, key):
            setattr(db_demande, key, value)

    if cadres is not None:
        db_demande.cadres.clear()
        for cadre in cadres:
            cadre_value = cadre.get("cadre") if isinstance(cadre, dict) else getattr(cadre, "cadre", None)
            if cadre_value:
                db_demande.cadres.append(DemandeTeamBuildingCadre(cadre=cadre_value))

    db.commit()
    db.refresh(db_demande)
    return get_demande_team_building(db, db_demande.id) or db_demande


def update_demande_team_building_statut(
    db: Session,
    db_demande: DemandeTeamBuilding,
    statut: str,
) -> DemandeTeamBuilding:
    db_demande.statut = statut
    db.commit()
    db.refresh(db_demande)
    return get_demande_team_building(db, db_demande.id) or db_demande


def delete_demande_team_building(db: Session, db_demande: DemandeTeamBuilding) -> None:
    db.delete(db_demande)
    db.commit()
