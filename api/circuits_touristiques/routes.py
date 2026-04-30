from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db
from crud import circuit_touristique as crud_circuit
from database.schemas import (
    CircuitTouristiqueCreate,
    CircuitTouristiqueRead,
    CircuitTouristiqueUpdate,
)
from security import get_current_user, require_module_access

router = APIRouter(prefix="/api/circuits-touristiques", tags=["circuits touristiques"])


def _nom_complet(user) -> str | None:
    if not user:
        return None
    return " ".join(filter(None, [getattr(user, "prenom", None), getattr(user, "nom", None)])) or None


def _serialize_circuit(circuit):
    return {
        "id": circuit.id,
        "titre": circuit.titre,
        "lieu": circuit.lieu,
        "thematique": circuit.thematique,
        "description": circuit.description,
        "details": circuit.details or [],
        "duree": circuit.duree,
        "prix_base": circuit.prix_base,
        "categorie": circuit.categorie,
        "type_circuit": circuit.type_circuit,
        "images": circuit.images or [],
        "itineraire": circuit.itineraire or [],
        "formules": circuit.formules or [],
        "inclus": circuit.inclus or [],
        "non_inclus": circuit.non_inclus or [],
        "conditions_annulation": circuit.conditions_annulation or [],
        "actif": circuit.actif,
        "publie": circuit.publie,
        "created_by_id": circuit.created_by_id,
        "updated_by_id": circuit.updated_by_id,
        "created_by_nom_complet": _nom_complet(getattr(circuit, "created_by", None)),
        "updated_by_nom_complet": _nom_complet(getattr(circuit, "updated_by", None)),
        "created_at": circuit.created_at,
        "updated_at": circuit.updated_at,
        "title": circuit.titre,
        "location": circuit.lieu,
        "thematic": circuit.thematique,
        "duration": circuit.duree,
        "price": circuit.prix_base,
        "category": circuit.categorie,
        "type": circuit.type_circuit,
        "itinerary": circuit.itineraire or [],
        "budget": circuit.formules or [],
        "included": circuit.inclus or [],
        "notIncluded": circuit.non_inclus or [],
        "cancellation": circuit.conditions_annulation or [],
    }


@router.get("/public", response_model=List[CircuitTouristiqueRead])
def get_public_circuits(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    circuits = crud_circuit.get_circuits_touristiques(db, skip=skip, limit=limit, only_published=True)
    return [_serialize_circuit(circuit) for circuit in circuits]


@router.get(
    "",
    response_model=List[CircuitTouristiqueRead],
    dependencies=[Depends(require_module_access("tourisme"))],
)
def get_circuits_touristiques(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    circuits = crud_circuit.get_circuits_touristiques(db, skip=skip, limit=limit)
    return [_serialize_circuit(circuit) for circuit in circuits]


@router.get(
    "/{circuit_id}",
    response_model=CircuitTouristiqueRead,
    dependencies=[Depends(require_module_access("tourisme"))],
)
def get_circuit_touristique(circuit_id: int, db: Session = Depends(get_db)):
    db_circuit = crud_circuit.get_circuit_touristique(db, circuit_id)
    if not db_circuit:
        raise HTTPException(status_code=404, detail="Circuit touristique non trouve")
    return _serialize_circuit(db_circuit)


@router.post("", response_model=CircuitTouristiqueRead, status_code=status.HTTP_201_CREATED)
def create_circuit_touristique(
    payload: CircuitTouristiqueCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_module_access("tourisme")),
):
    db_circuit = crud_circuit.create_circuit_touristique(
        db,
        payload,
        created_by_id=getattr(current_user, "id_utilisateur", None),
    )
    return _serialize_circuit(db_circuit)


@router.put("/{circuit_id}", response_model=CircuitTouristiqueRead)
def update_circuit_touristique(
    circuit_id: int,
    payload: CircuitTouristiqueUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    _=Depends(require_module_access("tourisme")),
):
    db_circuit = crud_circuit.get_circuit_touristique(db, circuit_id)
    if not db_circuit:
        raise HTTPException(status_code=404, detail="Circuit touristique non trouve")

    db_circuit = crud_circuit.update_circuit_touristique(
        db,
        db_circuit,
        payload,
        updated_by_id=getattr(current_user, "id_utilisateur", None),
    )
    return _serialize_circuit(db_circuit)


@router.delete("/{circuit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_circuit_touristique(
    circuit_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_module_access("tourisme")),
):
    db_circuit = crud_circuit.get_circuit_touristique(db, circuit_id)
    if not db_circuit:
        raise HTTPException(status_code=404, detail="Circuit touristique non trouve")
    crud_circuit.delete_circuit_touristique(db, db_circuit)
