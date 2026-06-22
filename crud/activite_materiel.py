from datetime import datetime
from typing import Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from database.models import Activite, ActiviteMateriel, Materiel
from database.schemas import ActiviteMaterielCreate, ActiviteMaterielUpdate

STATUTS_RESERVANT_MATERIEL = ("planifier", "en_preparation", "en_cours")


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def activite_reserve_materiel(statut: str | None) -> bool:
    return statut in STATUTS_RESERVANT_MATERIEL


def lock_materiel_reservation(db: Session, materiel_id: int) -> None:
    bind = db.get_bind()
    if bind is not None and bind.dialect.name == "postgresql":
        db.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": f"materiel-reservation-{materiel_id}"},
        )


def get_quantite_reservee(
    db: Session,
    materiel_id: int,
    date_debut: datetime,
    date_fin: datetime,
    exclude_activite_id: int | None = None,
) -> int:
    query = (
        db.query(func.coalesce(func.sum(ActiviteMateriel.quantite_prevue), 0))
        .join(Activite, Activite.id == ActiviteMateriel.activite_id)
        .filter(
            ActiviteMateriel.materiel_id == materiel_id,
            Activite.statut.in_(STATUTS_RESERVANT_MATERIEL),
            Activite.date_debut < date_fin,
            Activite.date_fin > date_debut,
        )
    )
    if exclude_activite_id is not None:
        query = query.filter(Activite.id != exclude_activite_id)

    return int(query.scalar() or 0)


def get_quantite_disponible(
    db: Session,
    db_materiel: Materiel,
    date_debut: datetime,
    date_fin: datetime,
    exclude_activite_id: int | None = None,
) -> int:
    quantite_reservee = get_quantite_reservee(
        db,
        db_materiel.id,
        date_debut,
        date_fin,
        exclude_activite_id=exclude_activite_id,
    )
    return max(0, int(db_materiel.quantite_disponible or 0) - quantite_reservee)


def get_max_quantite_reservee(db: Session, materiel_id: int) -> int:
    reservations = (
        db.query(ActiviteMateriel)
        .join(Activite, Activite.id == ActiviteMateriel.activite_id)
        .filter(
            ActiviteMateriel.materiel_id == materiel_id,
            Activite.statut.in_(STATUTS_RESERVANT_MATERIEL),
        )
        .all()
    )

    max_reservee = 0
    for reservation in reservations:
        activite = reservation.activite
        if not activite or not activite.date_debut or not activite.date_fin:
            continue
        max_reservee = max(
            max_reservee,
            get_quantite_reservee(
                db,
                materiel_id,
                activite.date_debut,
                activite.date_fin,
            ),
        )

    return max_reservee


def get_disponibilites_materiels(
    db: Session,
    date_debut: datetime,
    date_fin: datetime,
    exclude_activite_id: int | None = None,
) -> list[dict]:
    materiels = (
        db.query(Materiel)
        .filter(Materiel.statut.is_not(False))
        .order_by(Materiel.nom.asc())
        .all()
    )

    disponibilites = []
    for materiel in materiels:
        quantite_totale = int(materiel.quantite_disponible or 0)
        quantite_reservee = get_quantite_reservee(
            db,
            materiel.id,
            date_debut,
            date_fin,
            exclude_activite_id=exclude_activite_id,
        )
        disponibilites.append(
            {
                "materiel_id": materiel.id,
                "quantite_totale": quantite_totale,
                "quantite_reservee": quantite_reservee,
                "quantite_disponible": max(0, quantite_totale - quantite_reservee),
            }
        )

    return disponibilites


def get_activite_materiel(db: Session, activite_materiel_id: int) -> Optional[ActiviteMateriel]:
    return db.query(ActiviteMateriel).filter(ActiviteMateriel.id == activite_materiel_id).first()


def get_activite_materiel_by_pair(db: Session, activite_id: int, materiel_id: int) -> Optional[ActiviteMateriel]:
    return (
        db.query(ActiviteMateriel)
        .filter(
            ActiviteMateriel.activite_id == activite_id,
            ActiviteMateriel.materiel_id == materiel_id,
        )
        .first()
    )


def get_activites_materiels(db: Session, skip: int = 0, limit: int = 100) -> list[ActiviteMateriel]:
    return db.query(ActiviteMateriel).offset(skip).limit(limit).all()


def get_materiels_by_activite(db: Session, activite_id: int) -> list[ActiviteMateriel]:
    return db.query(ActiviteMateriel).filter(ActiviteMateriel.activite_id == activite_id).all()


def get_activites_by_materiel(db: Session, materiel_id: int, skip: int = 0, limit: int = 100) -> list[ActiviteMateriel]:
    return (
        db.query(ActiviteMateriel)
        .filter(ActiviteMateriel.materiel_id == materiel_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_activite_materiel(db: Session, payload: ActiviteMaterielCreate) -> ActiviteMateriel:
    db_activite_materiel = ActiviteMateriel(**_model_dump(payload))
    db.add(db_activite_materiel)
    db.commit()
    db.refresh(db_activite_materiel)
    return db_activite_materiel


def update_activite_materiel(
    db: Session,
    db_activite_materiel: ActiviteMateriel,
    payload: ActiviteMaterielUpdate | dict,
) -> ActiviteMateriel:
    updates = _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else dict(payload)
    for key, value in updates.items():
        if hasattr(db_activite_materiel, key):
            setattr(db_activite_materiel, key, value)
    db.commit()
    db.refresh(db_activite_materiel)
    return db_activite_materiel


def delete_activite_materiel(db: Session, db_activite_materiel: ActiviteMateriel) -> None:
    db.delete(db_activite_materiel)
    db.commit()
