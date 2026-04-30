from typing import Optional

from sqlalchemy.orm import Session, joinedload

from database.models import CircuitTouristique
from database.schemas import CircuitTouristiqueCreate, CircuitTouristiqueUpdate


def _model_dump(schema_obj, **kwargs):
    if hasattr(schema_obj, "model_dump"):
        return schema_obj.model_dump(**kwargs)
    return schema_obj.dict(**kwargs)


def get_circuit_touristique(db: Session, circuit_id: int) -> Optional[CircuitTouristique]:
    return (
        db.query(CircuitTouristique)
        .options(
            joinedload(CircuitTouristique.created_by),
            joinedload(CircuitTouristique.updated_by),
        )
        .filter(CircuitTouristique.id == circuit_id)
        .first()
    )


def get_circuits_touristiques(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    only_published: bool = False,
) -> list[CircuitTouristique]:
    query = db.query(CircuitTouristique).options(
        joinedload(CircuitTouristique.created_by),
        joinedload(CircuitTouristique.updated_by),
    )

    if only_published:
        query = query.filter(
            CircuitTouristique.actif == True,
            CircuitTouristique.publie == True,
        )

    return query.order_by(CircuitTouristique.created_at.desc()).offset(skip).limit(limit).all()


def create_circuit_touristique(
    db: Session,
    payload: CircuitTouristiqueCreate,
    created_by_id: int | None = None,
) -> CircuitTouristique:
    db_circuit = CircuitTouristique(**_model_dump(payload))
    db_circuit.created_by_id = created_by_id
    db_circuit.updated_by_id = created_by_id

    db.add(db_circuit)
    db.commit()
    db.refresh(db_circuit)
    return get_circuit_touristique(db, db_circuit.id) or db_circuit


def update_circuit_touristique(
    db: Session,
    db_circuit: CircuitTouristique,
    payload: CircuitTouristiqueUpdate,
    updated_by_id: int | None = None,
) -> CircuitTouristique:
    updates = _model_dump(payload, exclude_unset=True)

    for key, value in updates.items():
        setattr(db_circuit, key, value)

    db_circuit.updated_by_id = updated_by_id
    db.commit()
    db.refresh(db_circuit)
    return get_circuit_touristique(db, db_circuit.id) or db_circuit


def delete_circuit_touristique(db: Session, db_circuit: CircuitTouristique) -> None:
    db.delete(db_circuit)
    db.commit()
