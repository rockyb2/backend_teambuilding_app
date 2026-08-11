from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic import ValidationError
from smolagents import Tool
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload


BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")

from crud.circuit_touristique import (  # noqa: E402
    create_circuit_touristique,
    delete_circuit_touristique,
    get_circuit_touristique,
    update_circuit_touristique,
)
from database.connection import SessionLocal  # noqa: E402
from database.models import CircuitTouristique, CircuitTouristiqueTranslation  # noqa: E402
from database.schemas import CircuitTouristiqueCreate, CircuitTouristiqueUpdate  # noqa: E402


JSON_FIELDS = {
    "details",
    "images",
    "itineraire",
    "formules",
    "inclus",
    "non_inclus",
    "conditions_annulation",
}

FIELD_ALIASES = {
    "title": "titre",
    "location": "lieu",
    "thematic": "thematique",
    "theme": "thematique",
    "duration": "duree",
    "price": "prix_base",
    "category": "categorie",
    "type": "type_circuit",
    "itinerary": "itineraire",
    "program": "itineraire",
    "budget": "formules",
    "included": "inclus",
    "notIncluded": "non_inclus",
    "not_included": "non_inclus",
    "cancellation": "conditions_annulation",
    "is_active": "actif",
    "published": "publie",
}


def _json_response(ok: bool, **payload: Any) -> str:
    return json.dumps({"ok": ok, **payload}, ensure_ascii=False, default=str)


def _success(**payload: Any) -> str:
    return _json_response(True, **payload)


def _error(message: str, **payload: Any) -> str:
    return _json_response(False, error=message, **payload)


def _parse_json_object(raw_json: str, field_name: str) -> dict[str, Any]:
    try:
        value = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} doit être un objet JSON valide: {exc.msg}") from exc

    if not isinstance(value, dict):
        raise ValueError(f"{field_name} doit être un objet JSON.")

    return value


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _duration_from_days(value: Any) -> str | None:
    if value is None:
        return None
    try:
        days = int(value)
    except (TypeError, ValueError):
        return str(value)
    suffix = "jour" if days <= 1 else "jours"
    return f"{max(1, days)} {suffix}"


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)

    for old_key, new_key in FIELD_ALIASES.items():
        if old_key in normalized and new_key not in normalized:
            normalized[new_key] = normalized.pop(old_key)

    if "duration_days" in normalized and "duree" not in normalized:
        normalized["duree"] = _duration_from_days(normalized.pop("duration_days"))

    if "image_url" in normalized and "images" not in normalized:
        image_url = normalized.pop("image_url")
        normalized["images"] = [image_url] if image_url else []

    if "slug" in normalized and "thematique" not in normalized:
        normalized["thematique"] = str(normalized.pop("slug")).replace("-", " ")

    normalized.pop("translations", None)

    for field in JSON_FIELDS:
        if field in normalized:
            normalized[field] = _as_list(normalized[field])

    return normalized


def _summary(circuit: CircuitTouristique) -> dict[str, Any]:
    return {
        "id": circuit.id,
        "titre": circuit.titre,
        "lieu": circuit.lieu,
        "thematique": circuit.thematique,
        "duree": circuit.duree,
        "prix_base": circuit.prix_base,
        "categorie": circuit.categorie,
        "type_circuit": circuit.type_circuit,
        "actif": circuit.actif,
        "publie": circuit.publie,
        "created_at": circuit.created_at,
        "updated_at": circuit.updated_at,
    }


def _translation_to_dict(translation: CircuitTouristiqueTranslation) -> dict[str, Any]:
    return {
        "id": translation.id,
        "circuit_id": translation.circuit_id,
        "langue": translation.langue,
        "titre": translation.titre,
        "lieu": translation.lieu,
        "thematique": translation.thematique,
        "description": translation.description,
        "details": translation.details or [],
        "duree": translation.duree,
        "type_circuit": translation.type_circuit,
        "itineraire": translation.itineraire or [],
        "formules": translation.formules or [],
        "inclus": translation.inclus or [],
        "non_inclus": translation.non_inclus or [],
        "conditions_annulation": translation.conditions_annulation or [],
    }


def _circuit_to_dict(circuit: CircuitTouristique, include_translations: bool = True) -> dict[str, Any]:
    data = {
        **_summary(circuit),
        "description": circuit.description,
        "details": circuit.details or [],
        "images": circuit.images or [],
        "itineraire": circuit.itineraire or [],
        "formules": circuit.formules or [],
        "inclus": circuit.inclus or [],
        "non_inclus": circuit.non_inclus or [],
        "conditions_annulation": circuit.conditions_annulation or [],
        "created_by_id": circuit.created_by_id,
        "updated_by_id": circuit.updated_by_id,
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
    if include_translations:
        data["translations"] = [
            _translation_to_dict(translation)
            for translation in (circuit.translations or [])
        ]
    return data


class ListCircuitsTool(Tool):
    name = "list_circuits"
    description = "Liste les circuits touristiques du CRM avec leurs principaux champs."
    inputs = {
        "include_inactive": {
            "type": "boolean",
            "description": "Inclure les circuits inactifs.",
        },
        "limit": {
            "type": "integer",
            "description": "Nombre maximum de circuits à retourner, entre 1 et 100.",
        },
    }
    output_type = "string"

    def forward(self, include_inactive: bool, limit: int) -> str:
        limit = max(1, min(int(limit or 20), 100))
        with SessionLocal() as db:
            try:
                query = db.query(CircuitTouristique).options(
                    joinedload(CircuitTouristique.created_by),
                    joinedload(CircuitTouristique.updated_by),
                    joinedload(CircuitTouristique.translations),
                )
                if not include_inactive:
                    query = query.filter(CircuitTouristique.actif.is_(True))
                circuits = query.order_by(CircuitTouristique.created_at.desc()).limit(limit).all()
                return _success(
                    circuits=[_summary(circuit) for circuit in circuits],
                    count=len(circuits),
                )
            except SQLAlchemyError as exc:
                return _error("Erreur base de données.", details=str(exc))


class SearchCircuitsTool(Tool):
    name = "search_circuits"
    description = "Recherche des circuits par titre, lieu, thématique, description ou traduction."
    inputs = {
        "query": {
            "type": "string",
            "description": "Texte à rechercher.",
        },
        "include_inactive": {
            "type": "boolean",
            "description": "Inclure les circuits inactifs.",
        },
        "limit": {
            "type": "integer",
            "description": "Nombre maximum de résultats, entre 1 et 100.",
        },
    }
    output_type = "string"

    def forward(self, query: str, include_inactive: bool, limit: int) -> str:
        cleaned_query = str(query or "").strip()
        if not cleaned_query:
            return _error("La recherche ne peut pas être vide.")

        limit = max(1, min(int(limit or 20), 100))
        pattern = f"%{cleaned_query}%"

        with SessionLocal() as db:
            try:
                db_query = (
                    db.query(CircuitTouristique)
                    .outerjoin(CircuitTouristiqueTranslation)
                    .options(
                        joinedload(CircuitTouristique.created_by),
                        joinedload(CircuitTouristique.updated_by),
                        joinedload(CircuitTouristique.translations),
                    )
                    .filter(
                        or_(
                            CircuitTouristique.titre.ilike(pattern),
                            CircuitTouristique.lieu.ilike(pattern),
                            CircuitTouristique.thematique.ilike(pattern),
                            CircuitTouristique.description.ilike(pattern),
                            CircuitTouristiqueTranslation.titre.ilike(pattern),
                            CircuitTouristiqueTranslation.lieu.ilike(pattern),
                            CircuitTouristiqueTranslation.thematique.ilike(pattern),
                            CircuitTouristiqueTranslation.description.ilike(pattern),
                        )
                    )
                )
                if not include_inactive:
                    db_query = db_query.filter(CircuitTouristique.actif.is_(True))

                circuits = db_query.order_by(CircuitTouristique.id.asc()).limit(limit).all()
                return _success(
                    circuits=[_circuit_to_dict(circuit) for circuit in circuits],
                    count=len(circuits),
                )
            except SQLAlchemyError as exc:
                return _error("Erreur base de données.", details=str(exc))


class GetCircuitTool(Tool):
    name = "get_circuit"
    description = "Récupère un circuit touristique précis avec ses traductions."
    inputs = {
        "circuit_id": {
            "type": "integer",
            "description": "Identifiant du circuit touristique.",
        },
    }
    output_type = "string"

    def forward(self, circuit_id: int) -> str:
        with SessionLocal() as db:
            try:
                circuit = get_circuit_touristique(db, int(circuit_id))
                if circuit is None:
                    return _error("Circuit touristique introuvable.", circuit_id=circuit_id)
                return _success(circuit=_circuit_to_dict(circuit))
            except SQLAlchemyError as exc:
                return _error("Erreur base de données.", details=str(exc))


class CreateCircuitTool(Tool):
    name = "create_circuit"
    description = (
        "Crée un circuit touristique dans le CRM. "
        "circuit_json doit être un JSON au format CRM: titre, lieu, duree, prix_base, "
        "categorie, type_circuit, images, itineraire, formules, inclus, non_inclus, "
        "conditions_annulation, actif, publie. Les alias title, price, duration, "
        "location sont acceptés."
    )
    inputs = {
        "circuit_json": {
            "type": "string",
            "description": "Objet JSON représentant le circuit à créer.",
        },
    }
    output_type = "string"

    def forward(self, circuit_json: str) -> str:
        try:
            payload = _normalize_payload(_parse_json_object(circuit_json, "circuit_json"))
            schema = CircuitTouristiqueCreate(**payload)
        except ValueError as exc:
            return _error(str(exc))
        except ValidationError as exc:
            return _error("Données invalides.", details=exc.errors())

        with SessionLocal() as db:
            try:
                circuit = create_circuit_touristique(db, schema)
                return _success(circuit=_circuit_to_dict(circuit))
            except IntegrityError as exc:
                db.rollback()
                return _error("Création impossible: contrainte SQL violée.", details=str(exc.orig))
            except SQLAlchemyError as exc:
                db.rollback()
                return _error("Erreur base de données.", details=str(exc))


class UpdateCircuitTool(Tool):
    name = "update_circuit"
    description = (
        "Modifie un circuit touristique existant. "
        "patch_json doit contenir uniquement les champs à modifier. "
        "Les alias title, price, duration, location sont acceptés."
    )
    inputs = {
        "circuit_id": {
            "type": "integer",
            "description": "Identifiant du circuit à modifier.",
        },
        "patch_json": {
            "type": "string",
            "description": "Objet JSON contenant les champs à modifier.",
        },
    }
    output_type = "string"

    def forward(self, circuit_id: int, patch_json: str) -> str:
        try:
            payload = _normalize_payload(_parse_json_object(patch_json, "patch_json"))
            schema = CircuitTouristiqueUpdate(**payload)
            updates = schema.model_dump(exclude_unset=True) if hasattr(schema, "model_dump") else schema.dict(exclude_unset=True)
        except ValueError as exc:
            return _error(str(exc))
        except ValidationError as exc:
            return _error("Données invalides.", details=exc.errors())

        if not updates:
            return _error("Aucun champ de circuit à modifier.")

        with SessionLocal() as db:
            try:
                circuit = get_circuit_touristique(db, int(circuit_id))
                if circuit is None:
                    return _error("Circuit touristique introuvable.", circuit_id=circuit_id)
                updated = update_circuit_touristique(db, circuit, schema)
                return _success(circuit=_circuit_to_dict(updated))
            except IntegrityError as exc:
                db.rollback()
                return _error("Modification impossible: contrainte SQL violée.", details=str(exc.orig))
            except SQLAlchemyError as exc:
                db.rollback()
                return _error("Erreur base de données.", details=str(exc))


class DeleteCircuitTool(Tool):
    name = "delete_circuit"
    description = (
        "Supprime un circuit touristique. Utilise confirm=true uniquement si "
        "l'utilisateur a explicitement confirmé la suppression."
    )
    inputs = {
        "circuit_id": {
            "type": "integer",
            "description": "Identifiant du circuit à supprimer.",
        },
        "confirm": {
            "type": "boolean",
            "description": "True seulement après confirmation explicite de l'utilisateur.",
        },
    }
    output_type = "string"

    def forward(self, circuit_id: int, confirm: bool) -> str:
        if not confirm:
            return _error(
                "Confirmation obligatoire avant suppression.",
                next_action="Demande à l'utilisateur de confirmer explicitement la suppression.",
            )

        with SessionLocal() as db:
            try:
                circuit = get_circuit_touristique(db, int(circuit_id))
                if circuit is None:
                    return _error("Circuit touristique introuvable.", circuit_id=circuit_id)

                deleted = _circuit_to_dict(circuit)
                delete_circuit_touristique(db, circuit)
                return _success(deleted=deleted)
            except SQLAlchemyError as exc:
                db.rollback()
                return _error("Erreur base de données.", details=str(exc))


DATABASE_TOOLS = [
    ListCircuitsTool(),
    SearchCircuitsTool(),
    GetCircuitTool(),
    CreateCircuitTool(),
    UpdateCircuitTool(),
    DeleteCircuitTool(),
]

AGENT_TOOLS = DATABASE_TOOLS
