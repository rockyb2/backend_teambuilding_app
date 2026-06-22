from typing import Optional
from sqlalchemy.orm import Session, selectinload

from database.models import Jeu, JeuMateriel
from database.schemas import JeuCreate, JeuUpdate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def _normalize_jeu_data(data: dict) -> dict:
    normalized = dict(data)
    if "nb_participant_max" in normalized and "nb_max_participants" not in normalized:
        normalized["nb_max_participants"] = normalized["nb_participant_max"]
    if "nb_max_participants" in normalized and "nb_participant_max" not in normalized:
        normalized["nb_participant_max"] = normalized["nb_max_participants"]
    return normalized


def get_jeu(db: Session, jeu_id: int) -> Optional[Jeu]:
    return (
        db.query(Jeu)
        .options(selectinload(Jeu.materiels))
        .filter(Jeu.id_jeu == jeu_id)
        .first()
    )


def get_jeus(db: Session, skip: int = 0, limit: int = 100) -> list[Jeu]:
    return (
        db.query(Jeu)
        .options(selectinload(Jeu.materiels))
        .offset(skip)
        .limit(limit)
        .all()
    )


def _normalize_materiel_quantities(materiels: list[dict]) -> dict[int, int]:
    unique_materiels = {}
    for materiel in materiels:
        materiel_id = int(materiel["materiel_id"])
        quantite_requise = int(materiel.get("quantite_requise") or 1)
        if materiel_id <= 0 or quantite_requise <= 0:
            raise ValueError("Le matériel et sa quantité doivent être positifs")
        unique_materiels[materiel_id] = quantite_requise
    return unique_materiels


def _build_materiel_associations(materiels: list[dict]) -> list[JeuMateriel]:
    return [
        JeuMateriel(materiel_id=materiel_id, quantite_requise=quantite_requise)
        for materiel_id, quantite_requise in _normalize_materiel_quantities(materiels).items()
    ]


def _sync_materiel_associations(db_jeu: Jeu, materiels: list[dict]) -> None:
    desired = _normalize_materiel_quantities(materiels)
    existing = {association.materiel_id: association for association in db_jeu.materiels}

    for materiel_id, association in existing.items():
        if materiel_id not in desired:
            db_jeu.materiels.remove(association)

    for materiel_id, quantite_requise in desired.items():
        if materiel_id in existing:
            existing[materiel_id].quantite_requise = quantite_requise
        else:
            db_jeu.materiels.append(
                JeuMateriel(
                    materiel_id=materiel_id,
                    quantite_requise=quantite_requise,
                )
            )


def create_jeu(db: Session, payload: JeuCreate) -> Jeu:
    data = _normalize_jeu_data(_model_dump(payload))
    materiels = data.pop("materiels", [])
    db_jeu = Jeu(**data)
    db_jeu.materiels = _build_materiel_associations(materiels)
    db.add(db_jeu)
    db.commit()
    db.refresh(db_jeu)
    return get_jeu(db, db_jeu.id_jeu)


def update_jeu(db: Session, db_jeu: Jeu, payload: JeuUpdate | dict) -> Jeu:
    updates = _normalize_jeu_data(
        _model_dump(payload, exclude_unset=True) if not isinstance(payload, dict) else payload
    )
    materiels = updates.pop("materiels", None)
    for key, value in updates.items():
        if hasattr(db_jeu, key):
            setattr(db_jeu, key, value)
    if materiels is not None:
        _sync_materiel_associations(db_jeu, materiels)
    db.commit()
    db.refresh(db_jeu)
    return get_jeu(db, db_jeu.id_jeu)


def delete_jeu(db: Session, db_jeu: Jeu) -> None:
    db.delete(db_jeu)
    db.commit()
