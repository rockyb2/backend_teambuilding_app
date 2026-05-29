from typing import Optional

from sqlalchemy.orm import Session, joinedload

from database.models import CircuitTouristique, CircuitTouristiqueTranslation
from database.schemas import CircuitTouristiqueCreate, CircuitTouristiqueUpdate
from services.translation_service import translation_service


TRANSLATABLE_FIELDS = (
    "titre",
    "lieu",
    "thematique",
    "description",
    "details",
    "duree",
    "type_circuit",
    "itineraire",
    "formules",
    "inclus",
    "non_inclus",
    "conditions_annulation",
)

JSON_TRANSLATABLE_FIELDS = {
    "details",
    "itineraire",
    "formules",
    "inclus",
    "non_inclus",
    "conditions_annulation",
}


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
            joinedload(CircuitTouristique.translations),
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
        joinedload(CircuitTouristique.translations),
    )

    if only_published:
        query = query.filter(
            CircuitTouristique.actif == True,
            CircuitTouristique.publie == True,
        )

    return query.order_by(CircuitTouristique.created_at.desc()).offset(skip).limit(limit).all()


def _translation_payload_from_circuit(db_circuit: CircuitTouristique) -> dict:
    """Copie les champs qui doivent exister dans la table de traduction."""
    payload = {}
    for field in TRANSLATABLE_FIELDS:
        value = getattr(db_circuit, field)
        if field in JSON_TRANSLATABLE_FIELDS and value is None:
            value = []
        payload[field] = value
    return payload


def _translate_payload_to_english(payload: dict) -> dict:
    """Traduit seulement les champs texte; prix/images restent dans le circuit."""
    translated = {}
    for field, value in payload.items():
        translated[field] = translation_service.translate_value(value)
    return translated


def _upsert_translation(
    db: Session,
    circuit_id: int,
    langue: str,
    payload: dict,
) -> CircuitTouristiqueTranslation:
    """Cree ou met a jour la ligne d'une langue pour un circuit."""
    db_translation = (
        db.query(CircuitTouristiqueTranslation)
        .filter(
            CircuitTouristiqueTranslation.circuit_id == circuit_id,
            CircuitTouristiqueTranslation.langue == langue,
        )
        .first()
    )

    if db_translation is None:
        db_translation = CircuitTouristiqueTranslation(circuit_id=circuit_id, langue=langue)
        db.add(db_translation)

    for field, value in payload.items():
        setattr(db_translation, field, value)

    return db_translation


def _sync_translations(db: Session, db_circuit: CircuitTouristique) -> None:
    """Synchronise automatiquement le francais et l'anglais.

    - fr: copie exacte des champs saisis par l'admin.
    - en: version traduite par DeepL, avec fallback francais si DeepL est indisponible.
    """
    french_payload = _translation_payload_from_circuit(db_circuit)
    english_payload = _translate_payload_to_english(french_payload)

    _upsert_translation(db, db_circuit.id, "fr", french_payload)
    _upsert_translation(db, db_circuit.id, "en", english_payload)


def create_circuit_touristique(
    db: Session,
    payload: CircuitTouristiqueCreate,
    created_by_id: int | None = None,
) -> CircuitTouristique:
    db_circuit = CircuitTouristique(**_model_dump(payload))
    db_circuit.created_by_id = created_by_id
    db_circuit.updated_by_id = created_by_id

    db.add(db_circuit)
    db.flush()
    _sync_translations(db, db_circuit)
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
    should_sync_translations = any(field in updates for field in TRANSLATABLE_FIELDS)

    for key, value in updates.items():
        setattr(db_circuit, key, value)

    db_circuit.updated_by_id = updated_by_id
    if should_sync_translations:
        _sync_translations(db, db_circuit)

    db.commit()
    db.refresh(db_circuit)
    return get_circuit_touristique(db, db_circuit.id) or db_circuit


def delete_circuit_touristique(db: Session, db_circuit: CircuitTouristique) -> None:
    db.delete(db_circuit)
    db.commit()
