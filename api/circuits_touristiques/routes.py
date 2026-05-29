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


JSON_TRANSLATABLE_FIELDS = {
    "details",
    "itineraire",
    "formules",
    "inclus",
    "non_inclus",
    "conditions_annulation",
}


def _nom_complet(user) -> str | None:
    if not user:
        return None
    return " ".join(filter(None, [getattr(user, "prenom", None), getattr(user, "nom", None)])) or None


def _normalize_lang(lang: str | None) -> str:
    """Normalise fr-FR/en-US en fr/en pour matcher les lignes en BDD."""
    clean_lang = (lang or "fr").strip().lower()
    if not clean_lang:
        return "fr"
    return clean_lang.split("-", 1)[0][:10]


def _find_translation(circuit, lang: str | None):
    """Retourne la traduction demandee, puis fallback francais si besoin."""
    normalized_lang = _normalize_lang(lang)
    translations = getattr(circuit, "translations", None) or []

    for translation in translations:
        if translation.langue == normalized_lang:
            return translation

    if normalized_lang != "fr":
        for translation in translations:
            if translation.langue == "fr":
                return translation

    return None


def _translated_value(circuit, translation, field: str):
    """Lit d'abord la table translation, puis la table circuit en secours."""
    value = getattr(translation, field, None) if translation else None
    if value is not None:
        return value

    value = getattr(circuit, field)
    if field in JSON_TRANSLATABLE_FIELDS:
        return value or []
    return value


def _serialize_circuit(circuit, lang: str | None = "fr"):
    translation = _find_translation(circuit, lang)
    titre = _translated_value(circuit, translation, "titre")
    lieu = _translated_value(circuit, translation, "lieu")
    thematique = _translated_value(circuit, translation, "thematique")
    description = _translated_value(circuit, translation, "description")
    details = _translated_value(circuit, translation, "details")
    duree = _translated_value(circuit, translation, "duree")
    type_circuit = _translated_value(circuit, translation, "type_circuit")
    itineraire = _translated_value(circuit, translation, "itineraire")
    formules = _translated_value(circuit, translation, "formules")
    inclus = _translated_value(circuit, translation, "inclus")
    non_inclus = _translated_value(circuit, translation, "non_inclus")
    conditions_annulation = _translated_value(circuit, translation, "conditions_annulation")

    return {
        "id": circuit.id,
        "titre": titre,
        "lieu": lieu,
        "thematique": thematique,
        "description": description,
        "details": details or [],
        "duree": duree,
        "prix_base": circuit.prix_base,
        "categorie": circuit.categorie,
        "type_circuit": type_circuit,
        "images": circuit.images or [],
        "itineraire": itineraire or [],
        "formules": formules or [],
        "inclus": inclus or [],
        "non_inclus": non_inclus or [],
        "conditions_annulation": conditions_annulation or [],
        "actif": circuit.actif,
        "publie": circuit.publie,
        "created_by_id": circuit.created_by_id,
        "updated_by_id": circuit.updated_by_id,
        "created_by_nom_complet": _nom_complet(getattr(circuit, "created_by", None)),
        "updated_by_nom_complet": _nom_complet(getattr(circuit, "updated_by", None)),
        "created_at": circuit.created_at,
        "updated_at": circuit.updated_at,
        "title": titre,
        "location": lieu,
        "thematic": thematique,
        "duration": duree,
        "price": circuit.prix_base,
        "category": circuit.categorie,
        "type": type_circuit,
        "itinerary": itineraire or [],
        "budget": formules or [],
        "included": inclus or [],
        "notIncluded": non_inclus or [],
        "cancellation": conditions_annulation or [],
    }


@router.get("/public", response_model=List[CircuitTouristiqueRead])
def get_public_circuits(
    skip: int = 0,
    limit: int = 100,
    lang: str = "fr",
    db: Session = Depends(get_db),
):
    circuits = crud_circuit.get_circuits_touristiques(db, skip=skip, limit=limit, only_published=True)
    return [_serialize_circuit(circuit, lang=lang) for circuit in circuits]


@router.get(
    "",
    response_model=List[CircuitTouristiqueRead],
    dependencies=[Depends(require_module_access("tourisme"))],
)
def get_circuits_touristiques(
    skip: int = 0,
    limit: int = 100,
    lang: str = "fr",
    db: Session = Depends(get_db),
):
    circuits = crud_circuit.get_circuits_touristiques(db, skip=skip, limit=limit)
    return [_serialize_circuit(circuit, lang=lang) for circuit in circuits]


@router.get(
    "/{circuit_id}",
    response_model=CircuitTouristiqueRead,
    dependencies=[Depends(require_module_access("tourisme"))],
)
def get_circuit_touristique(
    circuit_id: int,
    lang: str = "fr",
    db: Session = Depends(get_db),
):
    db_circuit = crud_circuit.get_circuit_touristique(db, circuit_id)
    if not db_circuit:
        raise HTTPException(status_code=404, detail="Circuit touristique non trouve")
    return _serialize_circuit(db_circuit, lang=lang)


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
