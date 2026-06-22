from __future__ import annotations

import re
import uuid
from copy import deepcopy
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from database.models import DemandeTeamBuilding, Offre, Site
from services.proforma_pdf import calculate_totals


DEFAULT_PAYMENT_TERMS = "100% a la commande par cheque ou virement bancaire"
DEFAULT_AGENCY_DETAILS = [
    "Conception du programme",
    "Coordination operationnelle",
    "Encadrement equipe Ivoir Trips",
]

_SESSIONS: dict[str, dict[str, Any]] = {}


def _to_int_amount(value: Any) -> int | None:
    if value in (None, ""):
        return None
    cleaned = (
        str(value)
        .upper()
        .replace("FCFA", "")
        .replace("F CFA", "")
        .replace("XOF", "")
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
    )
    try:
        return int(Decimal(cleaned))
    except Exception:
        return None


def _tarif_value(tarifs: dict[str, Any] | None, *keys: str) -> int:
    if not isinstance(tarifs, dict):
        return 0
    for key in keys:
        if key in tarifs:
            return _to_int_amount(tarifs.get(key)) or 0
    return 0


def _parse_date(value: str) -> date | None:
    value = value.strip()
    for pattern, order in (
        (r"\b(\d{4})-(\d{2})-(\d{2})\b", "ymd"),
        (r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", "dmy"),
    ):
        match = re.search(pattern, value)
        if not match:
            continue
        parts = [int(part) for part in match.groups()]
        try:
            if order == "ymd":
                return date(parts[0], parts[1], parts[2])
            return date(parts[2], parts[1], parts[0])
        except ValueError:
            return None
    return None


def _base_fields() -> dict[str, Any]:
    return {
        "client": "",
        "nombre_personnes": None,
        "objet": "",
        "date_proforma": date.today(),
        "date_evenement": None,
        "lieu_souhaite": "",
        "budget_estime": None,
        "avec_salle": False,
        "restauration_incluse": False,
        "hebergement_inclus": False,
        "transport_inclus": False,
        "type_activite": "",
        "demande_team_building_id": None,
        "offre_id": None,
    }


def _apply_demande_context(fields: dict[str, Any], demande: DemandeTeamBuilding | None) -> None:
    if not demande:
        return
    fields["demande_team_building_id"] = demande.id
    fields["client"] = demande.entreprise or demande.nom_contact or fields["client"]
    fields["nombre_personnes"] = demande.nombre_participants or fields["nombre_personnes"]
    fields["objet"] = demande.type_activite or demande.objectif or fields["objet"]
    fields["date_evenement"] = demande.date_souhaitee or fields["date_evenement"]
    fields["lieu_souhaite"] = demande.lieu_souhaite or fields["lieu_souhaite"]
    fields["avec_salle"] = bool(demande.avec_salle)
    fields["restauration_incluse"] = bool(demande.restauration_incluse)
    fields["hebergement_inclus"] = bool(demande.hebergement_inclus or demande.avec_nuitee)
    fields["transport_inclus"] = bool(demande.transport_inclus)
    fields["type_activite"] = demande.type_activite or fields["type_activite"]


def _load_context(db: Session, demande_id: int | None, offre_id: int | None) -> dict[str, Any]:
    fields = _base_fields()
    if offre_id:
        offre = db.query(Offre).filter(Offre.id == offre_id).first()
        if offre:
            fields["offre_id"] = offre.id
            fields["objet"] = offre.titre or fields["objet"]
            fields["budget_estime"] = _to_int_amount(offre.montant_total) or fields["budget_estime"]
            _apply_demande_context(fields, offre.demande)
    if demande_id:
        demande = db.query(DemandeTeamBuilding).filter(DemandeTeamBuilding.id == demande_id).first()
        _apply_demande_context(fields, demande)
    return fields


def _parse_message_into_fields(message: str, fields: dict[str, Any]) -> None:
    text = message.strip()
    lowered = text.lower()

    participant_match = re.search(r"(\d{1,5})\s*(personnes|participants|pax|collaborateurs)", lowered)
    if participant_match:
        fields["nombre_personnes"] = int(participant_match.group(1))

    amount_match = re.search(r"(\d[\d\s.,]{2,})\s*(fcfa|f cfa|xof)", lowered)
    if amount_match:
        fields["budget_estime"] = _to_int_amount(amount_match.group(1))

    event_date = _parse_date(text)
    if event_date:
        fields["date_evenement"] = event_date

    client_match = re.search(r"(?:client|entreprise|societe|société)\s*[:\-]?\s*([A-Za-z0-9 '&._-]{2,80})", text, re.IGNORECASE)
    if client_match:
        fields["client"] = client_match.group(1).strip(" .")

    if "salle" in lowered or "seminaire" in lowered or "séminaire" in lowered:
        fields["avec_salle"] = True
    if any(word in lowered for word in ("restauration", "dejeuner", "déjeuner", "pause cafe", "pause café", "repas")):
        fields["restauration_incluse"] = True
    if any(word in lowered for word in ("hebergement", "hébergement", "nuitee", "nuitée", "hotel", "hôtel")):
        fields["hebergement_inclus"] = True
    if "transport" in lowered or "bus" in lowered:
        fields["transport_inclus"] = True

    if not fields.get("objet"):
        if "team building" in lowered:
            fields["objet"] = "Team building entreprise"
        elif "seminaire" in lowered or "séminaire" in lowered:
            fields["objet"] = "Seminaire entreprise"

    location_match = re.search(r"(?:lieu|a|à|sur)\s+([A-Za-z' -]{3,50})", text, re.IGNORECASE)
    if location_match and not fields.get("lieu_souhaite"):
        fields["lieu_souhaite"] = location_match.group(1).strip(" .")


def missing_fields(fields: dict[str, Any]) -> list[str]:
    missing = []
    if not fields.get("client"):
        missing.append("client")
    if not fields.get("nombre_personnes"):
        missing.append("nombre_personnes")
    if not fields.get("objet"):
        missing.append("objet")
    return missing


def _site_estimate(site: Site, fields: dict[str, Any]) -> tuple[int, list[dict[str, Any]]]:
    participants = int(fields.get("nombre_personnes") or 0)
    lines: list[dict[str, Any]] = []
    total = 0

    if fields.get("avec_salle") and site.a_salle_seminaire:
        room_price = _tarif_value(site.tarifs_seminaire, "journee", "tarif_journee", "demi_journee")
        if room_price:
            total += room_price
            lines.append({"designation": "Salle seminaire", "quantite": 1, "prix_unitaire": room_price, "montant_ht": room_price})

    if fields.get("restauration_incluse") and site.a_restauration:
        pause = _tarif_value(site.tarifs_restauration, "pause_cafe", "pause", "coffee_break")
        lunch = _tarif_value(site.tarifs_restauration, "dejeuner", "dej", "lunch")
        for label, price in (("Pause cafe", pause), ("Dejeuner", lunch)):
            if price:
                amount = price * participants
                total += amount
                lines.append({"designation": label, "quantite": participants, "prix_unitaire": price, "montant_ht": amount})

    return total, lines


def search_best_sites(db: Session, fields: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    participants = int(fields.get("nombre_personnes") or 0)
    budget = _to_int_amount(fields.get("budget_estime"))
    preferred_location = str(fields.get("lieu_souhaite") or "").lower()
    require_room = bool(fields.get("avec_salle"))
    require_food = bool(fields.get("restauration_incluse"))

    recommendations: list[dict[str, Any]] = []
    for site in db.query(Site).all():
        score = 40
        reasons: list[str] = []
        warnings: list[str] = []

        if site.capacite:
            if participants and site.capacite >= participants:
                score += 25
                reasons.append(f"Capacite adaptee ({site.capacite} places)")
            elif participants:
                score -= 45
                warnings.append(f"Capacite insuffisante ({site.capacite} places)")
        else:
            score += 4
            warnings.append("Capacite non renseignee")

        if require_room:
            if site.a_salle_seminaire:
                score += 18
                reasons.append("Salle seminaire disponible")
            else:
                score -= 30
                warnings.append("Salle seminaire non renseignee")

        if require_food:
            if site.a_restauration:
                score += 14
                reasons.append("Restauration disponible")
            else:
                score -= 25
                warnings.append("Restauration non renseignee")

        if preferred_location and site.localisation and preferred_location in site.localisation.lower():
            score += 12
            reasons.append("Localisation proche de la demande")

        estimate, lines = _site_estimate(site, fields)
        if budget and estimate:
            if estimate <= budget:
                score += 10
                reasons.append("Estimation compatible avec le budget")
            else:
                score -= 8
                warnings.append("Estimation au-dessus du budget indique")

        recommendations.append(
            {
                "site_id": site.id_site,
                "nom_site": site.nom_site,
                "localisation": site.localisation,
                "capacite": site.capacite,
                "type_site": site.type_site,
                "score": max(0, min(100, score)),
                "estimated_site_total": estimate,
                "reasons": reasons[:4],
                "warnings": warnings[:3],
                "lines": lines,
            }
        )

    return sorted(recommendations, key=lambda item: item["score"], reverse=True)[:limit]


def build_draft(fields: dict[str, Any], recommendations: list[dict[str, Any]]) -> dict[str, Any] | None:
    if missing_fields(fields):
        return None

    selected = recommendations[0] if recommendations else None
    prestations = deepcopy(selected.get("lines") or []) if selected else []
    if selected and not prestations:
        prestations.append(
            {
                "designation": f"Reservation et coordination site - {selected['nom_site']}",
                "quantite": 1,
                "prix_unitaire": 0,
                "montant_ht": 0,
            }
        )
    if not prestations:
        prestations.append(
            {
                "designation": "Prestation team building a parametrer",
                "quantite": 1,
                "prix_unitaire": 0,
                "montant_ht": 0,
            }
        )

    sections = [{"nom": "Logistique et site", "prestations": prestations}]
    subtotal = int(calculate_totals(sections)["sous_total_ht"])
    agency_fees = max(150000, int(subtotal * 0.10)) if subtotal else 150000

    draft = {
        "demande_team_building_id": fields.get("demande_team_building_id"),
        "offre_id": fields.get("offre_id"),
        "site_id": selected.get("site_id") if selected else None,
        "client": fields["client"],
        "nombre_personnes": fields["nombre_personnes"],
        "objet": fields["objet"],
        "date_proforma": fields.get("date_proforma") or date.today(),
        "date_evenement": fields.get("date_evenement"),
        "sections": sections,
        "frais_agence": agency_fees,
        "details_frais_agence": DEFAULT_AGENCY_DETAILS,
        "taux_tva_frais_agence": 18,
        "modalite_paiement": DEFAULT_PAYMENT_TERMS,
        "recommandations": recommendations,
        "notes": "Brouillon genere par l'assistant. A verifier avant generation PDF.",
        "statut": "validee",
    }
    totals = calculate_totals(draft["sections"], draft["frais_agence"], draft["taux_tva_frais_agence"])
    draft.update(
        {
            "sous_total_ht": int(totals["sous_total_ht"]),
            "tva_frais_agence": int(totals["tva_frais_agence"]),
            "total_ttc": int(totals["total_ttc"]),
        }
    )
    return draft


def _question_for_missing(field_name: str) -> str:
    questions = {
        "client": "Pour quel client ou quelle entreprise dois-je preparer la proforma ?",
        "nombre_personnes": "Combien de participants faut-il prevoir pour cette proforma ?",
        "objet": "Quel est l'objet exact de la prestation a proposer ?",
    }
    return questions.get(field_name, "Quelle information veux-tu ajouter a la proforma ?")


def _response_text(fields: dict[str, Any], missing: list[str], recommendations: list[dict[str, Any]], draft: dict[str, Any] | None) -> str:
    if missing:
        return _question_for_missing(missing[0])
    if draft:
        if recommendations:
            best = recommendations[0]
            return (
                f"J'ai prepare un brouillon avec {best['nom_site']} en recommandation principale "
                f"(score {best['score']}/100). Verifie les lignes et valide pour generer le PDF."
            )
        return "J'ai prepare un brouillon de proforma. Verifie les lignes et valide pour generer le PDF."
    return "J'ai mis a jour les informations. Ajoute les derniers details pour finaliser le brouillon."


def _session_response(session: dict[str, Any]) -> dict[str, Any]:
    missing = missing_fields(session["fields"])
    recommendations = search_best_sites(session["db"], session["fields"]) if not missing else []
    draft = build_draft(session["fields"], recommendations)
    return {
        "session_id": session["session_id"],
        "response": _response_text(session["fields"], missing, recommendations, draft),
        "collected_fields": session["fields"],
        "missing_fields": missing,
        "recommendations": recommendations,
        "draft": draft,
    }


def create_assistant_session(
    db: Session,
    user_id: int | None,
    demande_id: int | None = None,
    offre_id: int | None = None,
) -> dict[str, Any]:
    session_id = str(uuid.uuid4())
    fields = _load_context(db, demande_id, offre_id)
    session = {
        "session_id": session_id,
        "user_id": user_id,
        "fields": fields,
        "messages": [],
        "db": db,
    }
    _SESSIONS[session_id] = session
    response = _session_response(session)
    session.pop("db", None)
    return response


def handle_assistant_message(
    db: Session,
    session_id: str,
    message: str,
    user_id: int | None,
) -> dict[str, Any]:
    session = _SESSIONS.get(session_id)
    if not session:
        raise KeyError("Session assistant introuvable")
    if session.get("user_id") != user_id:
        raise PermissionError("Session assistant inaccessible")

    session["messages"].append({"role": "user", "content": message})
    _parse_message_into_fields(message, session["fields"])
    session["db"] = db
    response = _session_response(session)
    session.pop("db", None)
    session["messages"].append({"role": "assistant", "content": response["response"]})
    return response
